#!/usr/bin/env python
# Allow types to self-reference during their definitions.
from __future__ import annotations
import asyncio
import os
import re
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from abc import abstractmethod
from typing import Callable

from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.logging.logger import Logger
from mcp_agent.tracing.token_counter import TokenCounter
from mcp_agent.workflows.deep_orchestrator.config import (
    DeepOrchestratorConfig,
    ExecutionConfig,
    BudgetConfig,
)
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from dra.core.common.observer import Observer, Observers 
from dra.core.common.tasks import BaseTask, GenerateTask, AgentTask, TaskStatus
from dra.core.common.utils.strings import replace_variables, truncate
from dra.core.common.variables import Variable, VariableFormat
from dra.core.ux.display import Display

class DeepResearch():
    """
    Wrapper around mcp_agent for the deep research apps.
    """

    def_ux_title = "Deep Research Agent"

    def __init__(self,
            app_name: str,
            provider: str,
            config: DeepOrchestratorConfig,
            tasks: list[BaseTask],
            display: Display,
            observers: Observers,
            variables: dict[str, Variable]):
        self.app_name = app_name
        self.provider = provider
        self.config = config
        self.tasks = tasks
        self.output_dir_path = variables['output_dir_path'].value
        self.display = display
        self.observers = observers
        self.variables = variables

        # from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
        # self.llm_factory = OpenAIAugmentedLLM
        self.llm_factory = None
        match self.provider:
            case 'anthropic':
                from mcp_agent.workflows.llm.augmented_llm_anthropic import \
                    AnthropicAugmentedLLM
                self.llm_factory = AnthropicAugmentedLLM
            case 'openai' | 'ollama':
                from mcp_agent.workflows.llm.augmented_llm_openai import \
                    OpenAIAugmentedLLM
                self.llm_factory = OpenAIAugmentedLLM
            # case 'ollama':
            #     from mcp_agent.workflows.llm.augmented_llm_ollama import OllamaAugmentedLLM
            #     self.llm_factory = OllamaAIAugmentedLLM
            case _:
                raise ValueError(f"Unrecognized provider: {self.provider}")

        # These are lazily initialized in __finish_init!
        self.mcp_app: MCPApp | None = None
        self.orchestrator: DeepOrchestrator | None = None
        self.token_counter: TokenCounter | None = None
        self.logger: Logger | None = None

    # A observer loop that will be executed in its own thread.
    async def update_loop(self, update_iteration_frequency_secs: float = 1.0):
        while True:
            try:
                await self.observers.async_update()
                self.observers.update()
                await asyncio.sleep(update_iteration_frequency_secs)
            except Exception as e:
                err_msg = f"WARNING: Error updating observers: {e}"
                print(err_msg)
                if self.logger:
                    self.logger.warning(err_msg)
                break

    async def run(self):
        await self.__finish_init()

        verbose = Variable.get(self.variables.get('verbose'), False)
        if verbose:
            self.__print_details()

        update_iteration_frequency_secs = Variable.get(
            self.variables.get(
                'update_iteration_frequency_secs'), 1.0)

        async def do_work():

            # Start observer update loop
            update_task = asyncio.create_task(
                self.update_loop(
                    update_iteration_frequency_secs=update_iteration_frequency_secs))

            error_msg: str = None
            try:
                error_msg = await self.run_tasks()
            finally:
                # Final update...
                other = {'messages': [], 'error_msg': error_msg}
                await self.observers.async_update(is_final=True, other=other)
                self.observers.update(is_final=True, other=other)
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass

        await self.display.run_live(do_work)

    async def __finish_init(self):
        """
        Finish initializing the object by creating the MCApp, Orchestrator, the display, etc..
        This isn't done during __init__, because all components have to be constructed in a 
        particular order, so we can do this step asynchronously...
        """ 

        settings = self.__get_var_value('mcp_agent_config_path', None)
        if settings:
            settings = str(settings) # convert from Path to str.
        self.mcp_app = MCPApp(name=self.app_name, settings=settings)
        self.logger = self.mcp_app.logger

        async with self.mcp_app.run() as app:
            # Run the orchestrator
            # Create the Deep Orchestrator with configuration
            self.orchestrator = DeepOrchestrator(
                llm_factory=self.llm_factory,
                config=self.config,
                context=app.context,
            )
            # Store plan reference for display
            self.orchestrator.current_plan = None

            # Configure filesystem server with current directory
            app.context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

            # Due to an occasionally, apparent infinite loop bug when using ollama, we
            # don't invoke this code if serving that way.
            if (self.provider != "ollama"):
                self.token_counter = app.context.token_counter

            # Now let the observers know
            self.observers.update(self)

            self.logger.debug("Finished DeepResearch initialization")

    def add_observers(self, observers: dict[str, Observer]) -> dict[str, Observer]:
        """
        Add more observers and return the new dict of them. It is an error for a new
        key to match an existing key.
        """
        for key in observers.keys():
            if key in self.observers:
                raise ValueError("At least one key already exists in self.observers: current observers keys = {list(self.observers.keys())},  new observers keys = {list(observers.keys())}")
        self.observers.extend(observers)
        return self.observers

    def __get_value(self, key: str, default: any = None) -> any:
        return Variable.get_value(self.variables.get(key), default=default)

    async def run_tasks(self) -> str:
        """
        Iterate through `tasks`, where the results of previous
        tasks are passed as part of the next task's prompt via the
        `prompt_variables` passed to `Task.run()`.
        """
        previous_tasks_results = ''
        prompt_variables = dict([(v.key, v.value) for v in self.variables.values()])
        prompt_variables['previous_tasks_results'] = previous_tasks_results
        for task in self.tasks:
            status, result = await task.run(self.orchestrator, self.logger, **prompt_variables)            
            previous_tasks_results = f"{previous_tasks_results}\ntask {task.name} result:\n{result}\n"
            prompt_variables['previous_tasks_results'] = previous_tasks_results
            self.__save_task_raw_result(task.name, result)
            if not status == TaskStatus.FINISHED_OK:
                error_msg = f"Task sequence aborted due to failure of task {task.name}."
                self.logger.error(error_msg)
                return error_msg

        return ''
        
    def __save_task_raw_result(self, name: str, result: list[any]):
        result_file = self.output_dir_path / f"{name}_result.txt"
        self.logger.info(f"Writing 'raw' returned result for task {name} to: {result_file}")
        with open(result_file, "w") as file:
            for res in result:
                file.write(str(res))
                file.write('\n\n')
    
    def __print_details(self):
        message_fmt = "    {0:40s}  {1}"
        pwd = os.path.dirname(os.path.realpath(__file__))
        props_strs = []
        for key, l, v in Variable.make_formatted(self.variables.values(), variable_format=VariableFormat.PLAIN):
            props_strs.append(message_fmt.format(f"{l}:", v))
        props_str = "\n".join(props_strs)
        tasks_str = "\n".join([
            message_fmt.format(f"{n+1}:", str(self.tasks[n])) for n in range(len(self.tasks))
        ])
        message = f"""
{self.app_name}:
  Properties:
{props_str}  
  Tasks:
{tasks_str}  
"""
        print(message)
        self.logger.info(message)

        # Just to give the user time to see the above before the UX starts.
        time.sleep(2.0)  

    @staticmethod
    def make_default_config(
        short_run: bool,
        name: str,
        available_servers: list[str],
        variables: dict[str, Variable]) -> DeepOrchestratorConfig:
        """
        Create configuration for the Deep Orchestrator.
        TODO: Make all this user configurable. Not all the queries to `variables`
        are currently defined by the calling module! Hence, the hard-coded defaults
        here are used.
        """
        if short_run:
            # don't use the values passed in through variables.
            execution_config=ExecutionConfig(
                max_iterations=1,
                max_replans=2,
                max_task_retries=2,
                enable_parallel=True,
                enable_filesystem=True,
            )
            budget_config=BudgetConfig(
                max_tokens=1000,
                max_cost=0.10,
                max_time_minutes=1,
            )
        else:
            def get_val(key: str, default: any) -> any:
                return Variable.get(variables.get(key), default)

            execution_config=ExecutionConfig(
                max_iterations=get_val('max_iterations', 25),
                max_replans=get_val('max_replans', 2),
                max_task_retries=get_val('max_task_retries', 5),
                enable_parallel=get_val('enable_parallel', True),
                enable_filesystem=get_val('enable_filesystem', True),
            )
            budget_config=BudgetConfig(
                max_tokens=get_val('max_tokens', 100000),
                max_cost=get_val('max_cost_dollars', 1.00),
                max_time_minutes=get_val('max_time_minutes', 10),
            )
        config = DeepOrchestratorConfig(
            name=name,
            available_servers=available_servers,
            execution=execution_config,
            budget=budget_config,
        )
        return config

    def __get_var_value(self, key: str, default: any = None) -> any:
        if not self.variables:
            raise ValueError("Logic error: self.variables not yet initialized!")
        variable = self.variables.get(key)
        return variable.value if variable else default

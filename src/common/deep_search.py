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


from common.prompt_utils import load_prompt_markdown
from common.path_utils import resolve_path
from common.string_utils import replace_variables, truncate
from ux import Display

class TaskStatus(Enum):
    NOT_STARTED = 0
    RUNNING = 1
    """Returned normally (as best we can tell...)"""
    FINISHED_OK = 2
    """An error occurred, including an empty result from running the task."""
    FINISHED_ERROR = 3
    """An error occurred due to a thrown exception."""
    FINISHED_EXCEPTION = 4

class BaseTask():
    def __init__(self, 
        name: str, 
        title: str, 
        model_name: str, 
        prompt_path: Path,
        output_path: Path):
        self.name = name
        self.title = title
        self.model_name = model_name
        self.prompt_path = prompt_path
        self.output_path = output_path
        self.status: TaskStatus = TaskStatus.NOT_STARTED 
        self.result: list[any] = []

    async def run(self, 
        orchestrator: DeepOrchestrator,
        logger: Logger,
        **variables: dict[str,any]) -> (TaskStatus, list[any]):
        """
        Return the final status and the result, which are also attributes of the task object.
        """
        self.status = TaskStatus.RUNNING 
        try:
            self.task_prompt = self.prepare_task_prompt(logger, variables)
            if not variables.get('temperature'):
                variables['temperature'] = 0.7
            if not variables.get('max_iterations'):
                variables['max_iterations'] = 10
            self.result = await self._run(self.task_prompt, orchestrator, logger, **variables)
            if self.result:  # TBD: Probably doesn't catch all error scenarios!
                self.status = TaskStatus.FINISHED_OK
            else:
                self.status = TaskStatus.FINISHED_ERROR
                self.result = [f"No result for task {self.name}!"]
            self.__log_result(logger)
        except Exception as ex:
            self.status = TaskStatus.FINISHED_EXCEPTION
            self.result = [f"Exception {ex} thrown in task {self.name}!"]
            logger.error(str(self.result))
            raise ex
        return (self.status, self.result)

    @abstractmethod
    async def _run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        logger: Logger,
        **variables: dict[str,any]) -> list[any]:
        raise Exception("Abstract method BaseTask._run() called!")

    def __repr__(self) -> str: 
        return f"""name: {self.name}, model name: {self.model_name}, prompt path: {self.prompt_path}, status: {self.status}, result: {self.result}"""

    def prepare_task_prompt(self, logger: Logger, variables: dict[str,any]) -> str:
        """Load and format a task prompt."""
        prompt_template = load_prompt_markdown(self.prompt_path)
        task_prompt = replace_variables(prompt_template, **variables)
        if variables.get('verbose', False):
            task_prompt_save_file = self.output_path / f"{self.name}_task_prompt.txt"
            if logger:  # may not be initialized in tests...
                logger.info(f"Writing the {self.name} task prompt to {task_prompt_save_file}")
            with task_prompt_save_file.open('w') as file:
                file.write(f"This is the prompt that will be used for the {self.name} task:\n")
                file.write(task_prompt)
            
        return task_prompt

    def __log_result(self, logger: Logger):
        """
        Exceptions are handled in the except clause above, per
        the requirements for `Logger.exception(...)` invocation!
        This method is normally not called for other status values, but
        we handle them for "resilience".
        """
        match self.status:
            case TaskStatus.FINISHED_OK:
                logger.info(truncate(str(self.result), 2000, '...'))
            case TaskStatus.FINISHED_ERROR:
                logger.error(truncate(str(self.result), 2000, '...'))
            case _:
                msg = str(self.result) if self.result else 'No result yet...'
                logger.debug(f"{self.status}: {msg}")

class GenerateTask(BaseTask):
    def __init__(self, 
        name: str, 
        title: str, 
        model_name: str, 
        prompt_path: Path,
        output_path: Path):
        super().__init__(name, title, model_name, prompt_path, output_path)

    async def _run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        logger: Logger,
        **variables: dict[str,any]) -> list[any]:
        logger.debug("GenerateTask: calling inference")
        return await orchestrator.generate(
            message=task_prompt,
            request_params=RequestParams(
                model=self.model_name, 
                temperature=variables['temperature'],
                max_iterations=variables['max_iterations'],
            ),
        )

    def __repr__(self) -> str: 
        return f"""GenerateTask({super().__repr__()})"""
        
class AgentTask(BaseTask):
    def __init__(self, 
        name: str, 
        title: str, 
        model_name: str, 
        prompt_path: Path,
        output_path: Path,
        generate_prompt: str):
        super().__init__(name, title, model_name, prompt_path, output_path)
        self.generate_prompt = generate_prompt

    async def _run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        logger: Logger,
        **variables: dict[str,any]) -> list[any]:
        agent = Agent(
            name=self.name,
            instruction=task_prompt,
            context=orchestrator.context,
            server_names=[self.name]
        )

        async with agent:
            logger.debug("AgentTask: calling inference")
            llm = await agent.attach_llm(orchestrator.llm_factory)
            return await llm.generate(
                message=self.generate_prompt,
                request_params=RequestParams(
                    model=self.model_name, 
                    temperature=variables['temperature'],
                    max_iterations=variables['max_iterations'],
                ),
            )

    def __repr__(self) -> str: 
        return f"""AgentTask({super().__repr__()}, generate prompt: {self.generate_prompt})"""

class DeepSearch():
    """
    Wrapper around mcp_agent for the deep research apps.
    """
    def __init__(self,
            app_name: str,
            make_display: Callable[[DeepSearch], Display],
            config: DeepOrchestratorConfig,
            provider: str,
            tasks: list[BaseTask],
            output_path: str,
            variables: dict[str, any]):
        self.app_name = app_name
        self.make_display=make_display
        self.config = config
        self.provider = provider
        self.tasks = tasks
        self.output_path = output_path
        self.variables = variables

        self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M%:%S')

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
        self.display: Display | None = None
        self.mcp_app: MCPApp | None = None
        self.orchestrator: DeepOrchestrator | None = None
        self.token_counter: TokenCounter | None = None
        self.logger: Logger | None = None

    def properties(self) -> dict[str,any]:
        """Return a dictionary of the properties for this instance. Useful for reports."""
        return {
            "app_name": self.app_name,
            "config": self.config,
            "provider": self.provider,
            "tasks": self.tasks,
            "output_path": self.output_path,
            "variables": self.variables,
            "start_time": self.start_time,
        }

    async def run(self):
        await self.__finish_init()

        if self.variables.get('verbose', False):
            self.__print_details()

        # Setup the display loop...
        async def update_loop():
            while True:
                try:
                    self.display.update()
                    await asyncio.sleep(self.display.update_iteration_frequency_secs)
                except Exception as e:
                    self.logger.error(f"Display update error: {e}")
                    break

        async def do_work():
            # Start display update loop
            update_task = asyncio.create_task(update_loop())

            error_msg = ''
            try:
                error_msg = await self.run_tasks()
            finally:
                # Final display update...
                self.display.update()
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass

            # Final display of results and misc. app data...
            final_messages = [
                "\n",
                f"Finished: See output files under {self.output_path}.",
            ]
            self.display.report_results(error_msg)
            await self.display.final_update(final_messages)

        await self.display.run_live(do_work)

    async def __finish_init(self):
        """
        Finish initializing the object by creating the MCApp, Orchestrator, the display, etc..
        This isn't done during __init__, because all components have to be constructed in a 
        particular order, so we can do this step asynchronously...
        """ 

        self.mcp_app = MCPApp(name=self.app_name)
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

            self.token_counter = app.context.token_counter
            
            self.display = self.make_display(self, self.variables)
            self.logger.debug(str(self.display))

    async def run_tasks(self) -> str:
        """
        Iterate through `tasks`, where the results of previous
        tasks are passed as part of the next task's prompt.
        """
        self.variables['previous_tasks_results'] = ''

        for task in self.tasks:
            status, result = await task.run(self.orchestrator, self.logger, **self.variables)            
            previous_results = self.variables['previous_tasks_results']
            all_results = f"{previous_results}\ntask {task.name} result:\n{result}\n"
            self.variables.update({'previous_tasks_results': all_results})
            self.save_raw_result(task.name, result)
            if not status == TaskStatus.FINISHED_OK:
                error_msg = f"Task sequence aborted due to failure of task {task.name}."
                self.logger.error(error_msg)
                return error_msg

        return ''
        
    def save_raw_result(self, name: str, result: list[any]):
        result_file = f"{self.output_path}/{name}_result.txt"
        self.logger.info(f"Writing 'raw' returned result for task {name} to: {result_file}")
        with open(result_file, "w") as file:
            for res in result:
                file.write(str(res))
                file.write('\n\n')
    
    def __print_details(self):
        message_fmt = "    {0:25s}  {1}"
        pwd = os.path.dirname(os.path.realpath(__file__))
        props_str = "\n".join([
            message_fmt.format(f"{key}:", str(value)) for key, value in self.variables.items()
        ])
        tasks_str = "\n".join([
            message_fmt.format(f"{n+1}:", str(self.tasks[n])) for n in range(len(self.tasks))
        ])
        message = f"""
{self.app_name}:
  Tasks:
{tasks_str}  
  Properties:
{props_str}  
  UX:                    {self.variables.get('ux', "unknown!")}
  Output path:           {self.output_path}
  MCP Agent Config:      {self.config}
"""
        print(message)
        self.logger.info(message)

        # Just to give the user time to see the above before the UX starts.
        time.sleep(2.0)  

    @staticmethod
    def make_default_config(
        short_run: bool,
        name: str,
        available_servers: list[str]) -> DeepOrchestratorConfig:
        """Create configuration for the Deep Orchestrator"""
        if short_run:
            execution_config=ExecutionConfig(
                max_iterations=2,
                max_replans=2,
                max_task_retries=2,
                enable_parallel=True,
                enable_filesystem=True,
            )
            budget_config=BudgetConfig(
                max_tokens=10000,
                max_cost=0.20,
                max_time_minutes=2,
            )
        else:
            execution_config=ExecutionConfig(
                max_iterations=25,
                max_replans=2,
                max_task_retries=5,
                enable_parallel=True,
                enable_filesystem=True,
            )
            budget_config=BudgetConfig(
                max_tokens=100000,
                max_cost=1.00,
                max_time_minutes=10,
            )
        config = DeepOrchestratorConfig(
            name=name,
            available_servers=available_servers,
            execution=execution_config,
            budget=budget_config,
        )
        return config
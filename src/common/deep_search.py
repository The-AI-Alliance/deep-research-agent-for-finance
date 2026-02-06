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
from common.string_utils import replace_variables, truncate
from common.variables import Variable, VariableFormat
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
        prompt_template_path: Path,
        output_dir_path: Path,
        properties: dict[str,Variable]):
        self.name = name
        self.title = title
        self.model_name = model_name
        self.prompt_template_path = prompt_template_path
        self.output_dir_path = output_dir_path
        self.properties = properties

        self.status: TaskStatus = TaskStatus.NOT_STARTED 
        self.result: list[any] = []
        self.prompt = '' # lazy loaded...
        self.prompt_saved_file = self.output_dir_path / f"{self.name}_task_prompt.txt"

    async def run(self, 
        orchestrator: DeepOrchestrator,
        logger: Logger,
        **prompt_variables: dict[str,any]) -> (TaskStatus, list[any]):
        """
        Return the final status and the result, which are also attributes of the task object.
        """
        self.status = TaskStatus.RUNNING 
        try:
            self.prepare_prompt(logger, prompt_variables)
            self.result = await self._run(orchestrator, logger)
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
        orchestrator: DeepOrchestrator, 
        logger: Logger) -> list[any]:
        raise Exception("Abstract method BaseTask._run() called!")

    def attributes_as_strs(self, 
        which_formatting: VariableFormat = VariableFormat.PLAIN, 
        exclusions: set[str] = {}) -> dict[str,str]:
        """
        Return a dictionary of nicely-formatted labels and values for the attributes.
        The which_formatting flag let's you change styles, e.g., 'markdown' or 'plain'
        Optional exclude some attributes.
        """
        # First create a dictionary with the attribute names as keys and formatted values,
        # which we'll then filter for exclusions, then return a new dictionary with the
        # keys converted to nice labels.
        prompt = "No task prompt string!"
        result = "No task results!"
        if self.prompt:
            prompt = Variable('code', truncate(str(self.prompt), 200, '...'), kind='callout')
        if self.result:
            result = Variable('code', truncate(str(self.result), 200, '...'), kind='callout')

        vars = [
            Variable('name',                 self.name, kind='code'),
            Variable('title',                self.title),
            Variable('model_name',           self.model_name, kind='code'),
            Variable('prompt_template_path', self.prompt_template_path, kind='file'),
            Variable('prompt_saved_file',    self.prompt_saved_file, kind='file'),
            Variable('output_dir_path',      self.output_dir_path, kind='file'),
            Variable('status',               self.status.name, kind='code'),
        ]
        
        # TODO: somewhat fragile hard-coding these specific values:
        for key in ['temperature', 'max_iterations', 'max_tokens', 'max_cost_dollars', 'max_time_minutes']:
            value = self.properties.get(key)
            if value:
                vars.append = value

        # Put these two potentially long strings at the end.
        vars.extend([prompt, result])

        # Create a dictionary and remove the exclusions
        attrs1 = dict([(v.key, v) for v in vars])
        for ex in exclusions:
            attrs1.pop(ex)

        # Create and return a new dictionary, using the labels as keys and formatted
        # strings as values.
        attrs = dict([(l,s) for _, l, s in Variable.make_formatted(vars, variable_format=which_formatting)])
        return attrs

    def __repr__(self) -> str: 
        """This method omits the long prompt and results strings. See also attributes_as_strs()."""
        return f"""name: {self.name}, model name: {self.model_name}, prompt path: {self.prompt_template_path}, saved prompt file: {self.prompt_saved_file}, status: {self.status}, prompt: ..., result: ..."""

    def prepare_prompt(self, logger: Logger, prompt_variables: dict[str,str]) -> str:
        """Load and format a task prompt."""
        prompt_template = load_prompt_markdown(self.prompt_template_path)
        self.prompt = replace_variables(prompt_template, **prompt_variables)
        if logger:  # may not be initialized in tests...
            logger.info(f"Writing the {self.name} task prompt to {self.prompt_saved_file}")
        with self.prompt_saved_file.open('w') as file:
            file.write(f"This is the prompt that will be used for the {self.name} task:\n")
            file.write(self.prompt)
        return self.prompt

    def __log_result(self, logger: Logger):
        """
        Exceptions are handled in the except clause above, per
        the requirements for `Logger.exception(...)` invocation!
        This method is normally not called for other status values, but
        we handle them for "resilience".
        """
        result_str = 'No result yet...'
        if self.result:
            result_str = truncate(str(self.result), 2000, '...')            
        msg = f"""Task "{self.name}": status = {self.status}), result = {result_str}"""
        match self.status:
            case TaskStatus.FINISHED_ERROR | TaskStatus.FINISHED_EXCEPTION:
                logger.error(f"""ERROR! {msg}""")
            case _:
                logger.info(msg)

    def _get_val(self, key: str, default: any) -> any:
        return Variable.get(self.properties.get(key), default)

class GenerateTask(BaseTask):
    def __init__(self, 
        name: str, 
        title: str, 
        model_name: str, 
        prompt_template_path: Path,
        output_dir_path: Path,
        properties: dict[str,any]):
        super().__init__(name, title, model_name, 
            prompt_template_path, output_dir_path, 
            properties)

    async def _run(self, 
        orchestrator: DeepOrchestrator, 
        logger: Logger) -> list[any]:
        logger.debug("GenerateTask: calling inference")
        return await orchestrator.generate(
            message=self.prompt,
            request_params=RequestParams(
                model=self.model_name, 
                temperature=self._get_val('temperature', 0.7),
                max_iterations=self._get_val('max_iterations', 10),
                max_tokens=self._get_val('max_tokens', 100000),
                max_cost=self._get_val('max_cost_dollars', 2.0),
                max_time_minutes=self._get_val('max_time_minutes', 10),
            ),
        )

    def __repr__(self) -> str: 
        return f"""GenerateTask({super().__repr__()})"""
        
class AgentTask(BaseTask):
    def __init__(self, 
        name: str, 
        title: str, 
        model_name: str, 
        prompt_template_path: Path,
        output_dir_path: Path,
        generate_prompt: str,
        properties: dict[str,any]):
        super().__init__(name, title, model_name, 
            prompt_template_path, output_dir_path, 
            properties)
        self.generate_prompt = generate_prompt

    async def _run(self, 
        prompt: str, 
        orchestrator: DeepOrchestrator, 
        logger: Logger) -> list[any]:
        agent = Agent(
            name=self.name,
            instruction=prompt,
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
                    temperature=self._get_val('temperature', 0.7),
                    max_iterations=self._get_val('max_iterations', 10),
                    max_tokens=self._get_val('max_tokens', 100000),
                    max_cost=self._get_val('max_cost_dollars', 2.0),
                    max_time_minutes=self._get_val('max_time_minutes', 10),
                ),
            )

    def attributes_as_strs(self, which_formatting: VariableFormat = VariableFormat.PLAIN, exclusions: set[str] = {}) -> dict[str,str]:
        d = super().attributes_as_strs(exclusions)
        if 'generate_prompt' not in exclusions:
            var = Variable('generate_prompt', self.generate_prompt)
            _, label, value_str = var.format()
            d[label] = value_str
        return d

    def __repr__(self) -> str: 
        return f"""AgentTask({super().__repr__()}, generate prompt: {self.generate_prompt})"""

class DeepSearch():
    """
    Wrapper around mcp_agent for the deep research apps.
    """
    def __init__(self,
            app_name: str,
            make_display: Callable[[DeepSearch, dict[str, Variable]], Display],
            config: DeepOrchestratorConfig,
            provider: str,
            tasks: list[BaseTask],
            output_dir_path: Path,
            variables: dict[str, Variable]):
        self.app_name = app_name
        self.make_display=make_display
        self.config = config
        self.provider = provider
        self.tasks = tasks
        self.output_dir_path = output_dir_path
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
        self.display: Display | None = None
        self.mcp_app: MCPApp | None = None
        self.orchestrator: DeepOrchestrator | None = None
        self.token_counter: TokenCounter | None = None
        self.logger: Logger | None = None

    async def run(self):
        await self.__finish_init()

        verbose = self.variables.get('verbose', Variable('verbose', False))
        if verbose.value:
            self.__print_details()

        update_iteration_frequency_secs = variables.get(
            'update_iteration_frequency_secs', 1.0)

        async def do_work():
            # Final message at the end...
            final_messages = [
                "\n",
                f"Finished: See output files under {self.output_dir_path}.",
            ]

            # Start display update loop
            update_task = asyncio.create_task(self.display.update_loop())

            error_msg: str = None
            try:
                error_msg = await self.run_tasks()
            finally:
                # Final display update...
                self.display.update(final=True)
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass

            await self.display.final_update(final_messages, error_msg)

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
                max_tokens=10000,
                max_cost=0.20,
                max_time_minutes=2,
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
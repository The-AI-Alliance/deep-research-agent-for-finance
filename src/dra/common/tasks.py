#!/usr/bin/env python
# Allow types to self-reference during their definitions.
from __future__ import annotations

from enum import Enum
from pathlib import Path
from abc import abstractmethod

from mcp_agent.agents.agent import Agent
from mcp_agent.logging.logger import Logger
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.llm.augmented_llm import RequestParams


from dra.common.utils.prompts import load_prompt_markdown
from dra.common.utils.strings import replace_variables, truncate
from dra.common.variables import Variable, VariableFormat

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
        variable_format: VariableFormat = VariableFormat.PLAIN, 
        exclusions: set[str] = {}) -> dict[str,str]:
        """
        Return a dictionary of nicely-formatted labels and values for the attributes.
        The variable_format flag let's you change styles, e.g., 'markdown' or 'plain'
        Optional exclude some attributes.
        """
        # First create a dictionary with the attribute names as keys and formatted values,
        # which we'll then filter for exclusions, then return a new dictionary with the
        # keys converted to nice labels.
        prompt_str = "No task prompt string!"
        result_str = "No task results!"
        if self.prompt:
            prompt_str = truncate(str(self.prompt), 200, '...')
        if self.result:
            result_str = truncate(str(self.result), 200, '...')
        
        prompt = Variable('code', prompt_str, kind='callout')
        result = Variable('code', result_str, kind='callout')

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
                vars.append(value)

        # Put these two potentially long strings at the end.
        vars.extend([prompt, result])

        # Create a dictionary and remove the exclusions
        attrs1 = dict([(v.key, v) for v in vars])
        for ex in exclusions:
            attrs1.pop(ex)

        # Create and return a new dictionary, using the labels as keys and formatted
        # strings as values.
        attrs = dict([(l,s) for _, l, s in Variable.make_formatted(vars, variable_format=variable_format)])
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
        orchestrator: DeepOrchestrator, 
        logger: Logger) -> list[any]:
        agent = Agent(
            name=self.name,
            instruction=self.prompt,
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

    def attributes_as_strs(self, variable_format: VariableFormat = VariableFormat.PLAIN, exclusions: set[str] = {}) -> dict[str,str]:
        d = super().attributes_as_strs(variable_format=variable_format, exclusions=exclusions)
        if 'generate_prompt' not in exclusions:
            var = Variable('generate_prompt', self.generate_prompt)
            _, label, value_str = var.format(variable_format=variable_format)
            d[label] = value_str
        return d

    def __repr__(self) -> str: 
        return f"""AgentTask({super().__repr__()}, generate prompt: {self.generate_prompt})"""


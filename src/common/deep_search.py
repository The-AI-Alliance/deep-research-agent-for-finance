#!/usr/bin/env python
import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.logging.logger import Logger
from mcp_agent.tracing.token_counter import TokenCounter
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from common.prompt_utils import load_prompt_markdown
from common.path_utils import resolve_path
from common.string_utils import replace_variables


class BaseTask():
    def __init__(self, 
        name: str, 
        model_name: str, 
        prompt_path: Path):
        self.name = name
        self.model_name = model_name
        self.prompt_path = prompt_path
        self.result: str = ''

    async def run(self, 
        orchestrator: DeepOrchestrator,
        **variables: dict[str,any]) -> any:
        self.task_prompt = self.prepare_task_prompt(key, prompt_path, **variables)
        temperature=variables.get('temperature', 0.7),
        max_iterations=variables.get('max_iterations', 10)
        self.result = __run(self, task_prompt, orchestrator, temperature, max_iterations, **variables)
        return self.result

    @abstractmethod
    async def __run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        temperature: float,
        max_iterations: int,
        **variables: dict[str,any]) -> any:

class GenerateTask(BaseTask):
    def __init__(self, 
        name: str, 
        model_name: str, 
        prompt_path: Path):
        self.super().__init__(name, model_name, prompt_path)

    async def __run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        temperature: float,
        max_iterations: int,
        **variables: dict[str,any]) -> any:
        result = await orchestrator.generate(
            message=task_prompt,
            request_params=RequestParams(
                model=self.model_name, 
                temperature=temperature,
                max_iterations=max_iterations,
            ),
        )
        return result

class AgentTask(BaseTask):
    def __init__(self, 
            name: str, 
            model_name: str, 
            prompt_path: Path,
            generate_prompt: str):
        self.super().__init__(name, model_name, prompt_path)
        self.generate_prompt = generate_prompt

    async def __run(self, 
        task_prompt: str, 
        orchestrator: DeepOrchestrator, 
        temperature: float,
        max_iterations: int,
        **variables: dict[str,any]) -> any:
        agent = Agent(
            name=self.name,
            instruction=task_prompt,
            context=orchestrator.context,
            server_names=[self.name]
        )

        async with agent:
            llm = await agent.attach_llm(orchestrator.llm_factory)

            result = await llm.generate(
                message=self.generate_prompt,
                request_params=RequestParams(
                    model=self.model_name, 
                    temperature=temperature,
                    max_iterations=max_iterations
                ),
            )
            return result

class DeepSearch():
    """
    Wrapper around mcp_agent for the deep research apps.
    """
    def __init__(self,
            app_name: str,
            config: DeepOrchestratorConfig,
            provider: str,
            tasks: list[BaseTask],
            output_path: str,
            variables: dict[str, any]):
        self.app_name = app_name
        self.config = config
        self.provider = provider
        self.tasks = tasks
        self.variables = variables
        self.output_path = output_path
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


        # These are lazily initialized!
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

    async def setup(self) -> MCPApp:
        # Initialize MCP App.
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
            self.logger = app.logger
            return app

    async def run(self) -> dict[str, any]:
        """
        Iterate through `tasks`, where the results of previous
        tasks are passed as part of the next task's prompt.
        """
        results: dict[str, any] = {}
        variables['previous_tasks_results'] = ''

        for task in self.tasks:
            # Load and format the next task's prompt
            task_prompt = self.prepare_task_prompt(task.name, task.prompt_path, **variables)
            result = task.run(self.orchestrator, **variables)
            
            results[task.name] = result
            previous_results = variables['previous_tasks_results']
            all_results = f"{previous_results}\n\ntask {task.name} result:\n{result}"
            variables.update({'previous_tasks_results': all_results})

            self.save_raw_result(task.name, result)

        return results
        
    def save_raw_result(self, name: str, result: str):
        result_file = f"{self.output_path}/{name}_result.txt"
        self.logger.info(f"Writing 'raw' returned result for task {name} to: {result_file}")
        with open(result_file, "w") as file:
            file.write(str(result))

    def prepare_task_prompt(self, name: str, prompt_file_path: Path, variables: dist[str,any]) -> str:
        """Load and format a task prompt."""
        prompt_template = load_prompt_markdown(prompt_file_path)
        task_prompt = replace_variables(prompt_template, **variables)
        if variables.get('verbose', False):
            task_prompt_save_file = f"{self.output_path}/{name}_task_prompt.txt"
            if self.logger:  # may not be initialized in tests...
                self.logger.info(f"Writing the {name} task prompt to {task_prompt_save_file}")
            with open(task_prompt_save_file, 'w') as file:
                file.write(f"This is the prompt that will be used for the {name} task:\n")
                file.write(task_prompt)
            
        return task_prompt

#!/usr/bin/env python
"""
The Markdown-formatted streaming output version of Deep Orchestrator Finance Research Example
"""

import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path, PosixPath
from typing import Any

from mcp_agent.agents.agent import Agent
from mcp_agent.app import MCPApp
from mcp_agent.logging.logger import Logger
from mcp_agent.tracing.token_counter import TokenCounter
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.llm.augmented_llm import RequestParams

from finance_deep_search.prompts import load_prompt_markdown
from finance_deep_search.string_utils import replace_variables


class DeepSearch():
    """
    Wrapper around mcp_agent for the deep research app.
    See the help in main.py for details and requirements for
    the arguments used to construct instances.
    """
    def __init__(self,
            app_name: str,
            config: DeepOrchestratorConfig,
            ticker: str,
            company_name: str,
            reporting_currency: str,
            orchestrator_model_name: str,
            excel_writer_model_name: str,
            provider: str,
            prompts_path: str,
            financial_research_prompt_path: str,
            excel_writer_agent_prompt_path: str,
            output_path: str,
            output_spreadsheet_path: str,
            short_run: bool = False,
            verbose: bool = False):
        self.app_name = app_name
        self.config = config
        self.ticker = ticker
        self.company_name = company_name
        self.reporting_currency = reporting_currency
        self.orchestrator_model_name = orchestrator_model_name
        self.excel_writer_model_name = excel_writer_model_name
        self.provider = provider
        self.output_path = output_path
        self.output_spreadsheet_path = output_spreadsheet_path
        self.short_run = short_run
        self.verbose = verbose
        self.start_time = datetime.now().strftime('%Y-%m-%d %H:%M%:%S')

        self.prompts_path: Path = Path(prompts_path)
        self.financial_research_prompt_path: Path = self.__resolve_path(
            financial_research_prompt_path, self.prompts_path)
        self.excel_writer_agent_prompt_path: Path = self.__resolve_path(
            excel_writer_agent_prompt_path, self.prompts_path)

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

    def properties(self) -> dict[str,Any]:
        """Return a dictionary of the properties for this instance. Useful for reports."""
        return {
            "app_name": self.app_name,
            "config": self.config,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "reporting_currency": self.reporting_currency,
            "orchestrator_model_name": self.orchestrator_model_name,
            "excel_writer_model_name": self.excel_writer_model_name,
            "provider": self.provider,
            "output_path": self.output_path,
            "output_spreadsheet_path": self.output_spreadsheet_path,
            "prompts_path": self.prompts_path,
            "financial_research_prompt_path": self.financial_research_prompt_path,
            "excel_writer_agent_prompt_path": self.excel_writer_agent_prompt_path,
            "start_time": self.start_time,
            "short_run": self.short_run,
        }

    def __resolve_path(self, path_str: str, possible_parent: Path) -> Path:
        path = Path(path_str)
        if path.parents[0] == PosixPath('.'):
            return possible_parent / path
        else:
            return path

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
    
    async def run(self) -> dict[str,str]:
        results = {}

        # Load and format the financial research task prompt
        financial_research_task_prompt = self.prepare_financial_research_task_prompt()

        max_iterations = 1 if self.short_run else 10

        research_result = await self.orchestrator.generate_str(
            message=financial_research_task_prompt,
            request_params=RequestParams(
                model=self.orchestrator_model_name, 
                temperature=0.7, 
                max_iterations=max_iterations
            ),
        )
        results['research'] = research_result
        rr_file = f"{self.output_path}/research_result.txt"
        self.logger.info(f"Writing 'raw' returned research result to: {rr_file}")
        with open(rr_file, "w") as file:
            for line in research_result.split('\n'):
                file.write(line)

        # The Excel writer task prompt
        excel_task_prompt = self.prepare_excel_task_prompt(research_result)

        excel_agent = Agent(
            name="ExcelWriter",
            instruction=excel_task_prompt,
            context=self.orchestrator.context,
            server_names=["excel"]
        )

        async with excel_agent:
            excel_llm = await excel_agent.attach_llm(
                self.llm_factory
            )

            excel_result = await excel_llm.generate_str(
                message="Generate the Excel file with the provided financial data.",
                request_params=RequestParams(
                    model=self.excel_writer_model_name, 
                    temperature=0.7, 
                    max_iterations=max_iterations
                ),
            )
            results['excel'] = excel_result
            er_file = f"{self.output_path}/excel_result.txt"
            self.logger.info(f"Writing 'raw' returned Excel result to: {er_file}")
            with open(er_file, "w") as file:
                file.write(excel_result)

        return results

    def prepare_financial_research_task_prompt(self) -> str:
        """Load and format the financial task research task prompt."""
        financial_research_task_prompt_template = load_prompt_markdown(
            self.financial_research_prompt_path)
        financial_research_task_prompt = replace_variables(
            financial_research_task_prompt_template,
            ticker=self.ticker,
            company_name=self.company_name,
            reporting_currency=self.reporting_currency, 
            units=f"{self.reporting_currency} millions",
            output_path=self.output_path,
        )
        financial_research_task_prompt_file = f"{self.output_path}/financial_research_task_prompt.txt"
        if self.logger:  # may not be initialized in tests...
            self.logger.info(f"Writing the financial deep research task prompt to {financial_research_task_prompt_file}")
        with open(financial_research_task_prompt_file, 'w') as file:
            file.write("This is the prompt that will be used for the financial deep research:\n")
            file.write(financial_research_task_prompt)
        return financial_research_task_prompt

    def prepare_excel_task_prompt(self, research_result: str) -> str:
        """The Excel writer task prompt."""
        excel_task_prompt_template = load_prompt_markdown(
            self.excel_writer_agent_prompt_path)
        excel_task_prompt = replace_variables(
            excel_task_prompt_template,
            financial_data=research_result,
            ticker=self.ticker,
            company_name=self.company_name,
            reporting_currency=self.reporting_currency, 
            units=f"{self.reporting_currency} millions",
            output_path=self.output_path,
            output_spreadsheet_path=self.output_spreadsheet_path,
        )
        excel_task_prompt_file = f"{self.output_path}/excel_task_prompt.txt"
        if self.logger:  # may not be initialized in tests...
            self.logger.info(f"Writing the excel service task prompt to {excel_task_prompt_file}")
        with open(excel_task_prompt_file, 'w') as file:
            file.write("This is the prompt that will be sent to the excel service:\n")
            file.write(excel_task_prompt)
        return excel_task_prompt

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

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import (
    DeepOrchestratorConfig,
    ExecutionConfig,
    BudgetConfig,
    PolicyConfig,
    ContextConfig,
    CacheConfig,
)
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams


class DeepSearch():

    def __init__(
            app_name: str,
            config: DeepOrchestratorConfig,
            ticker: str,
            company_name: str,
            orchestrator_model_name: str,
            excel_writer_model_name: str,
            prompts_path: str,
            financial_research_prompt_path: str,
            excel_writer_agent_prompt_path: str,
            output_path: str,
            verbose: bool,
            noop: bool):
        self.app_name: str = app_name
        self.config: DeepOrchestratorConfig = config,
        self.ticker: str = ticker
        self.company_name: str = company_name
        self.orchestrator_model_name: str = orchestrator_model_name
        self.excel_writer_model_name: str = excel_writer_model_name
        self.output_path: str = output_path
        self.verbose: bool = verbose
        self.noop: bool = noop

        self.prompts_path: Path = Path(prompts_path)
        self.financial_research_prompt_path: Path = 
            self.__resolve_path(financial_research_prompt_path, prompts_path)
        self.excel_writer_agent_prompt_path: Path = 
            self.__resolve_path(excel_writer_agent_prompt_path, prompts_path)

        self.orchestrator = None
        self.token_counter = None
        
        # Hold the results...
        self.research_result = None
        self.excel_result = None

        if noop:
            print(f"Inside DeepSearch. Returning...")
            return

        # Initialize MCP App.
        self.mcp_app = MCPApp(name=app_name)


        # Load and format the financial research task prompt
        financial_prompt = load_prompt_markdown(
            self.financial_research_prompt_path)
        self.financial_task_prompt = format_prompt(
            financial_prompt,
            company_name=company_name,
            ticker=ticker, 
            units="$ millions"
        )

        # Load and format the Excel agent prompt
        excel_prompt = load_prompt_markdown(
            self.excel_writer_agent_prompt_path)
        self.excel_instruction = format_prompt(
            excel_prompt,
            stock_ticker=ticker,
            output_path=output_path,
            financial_data=result
        )

    def __resolve_path(path_str: str, possible_parent: Path) -> Path:
        path = Path(path_str)
        if path.parents[0] == PosixPath('.'):
            return possible_parent / path
        else:
            return path

    async def run() -> DeepSearch:
        """
        The `update_loop` argument is called whenever the UX 
        needs to be updated with new content.
        """
        async with self.mcp_app.run() as app:
            context = app.context
            logger = app.logger
            self.token_counter = context.token_counter

            # Configure filesystem server with current directory
            context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

            # Create the Deep Orchestrator with configuration
            self.orchestrator = DeepOrchestrator(
                llm_factory=OpenAIAugmentedLLM,
                config=config,
                context=context,
            )
            
            # Store plan reference for display
            orchestrator.current_plan = None

            # Run the orchestrator

            self.research_result = await orchestrator.generate_str(
                message=self.financial_task_prompt,
                request_params=RequestParams(
                    model=self.orchestrator_model_name, 
                    temperature=0.7, 
                    max_iterations=10
                ),
            )

            excel_agent = Agent(
                name="ExcelWriter",
                instruction=self.excel_instruction,
                context=context,
                server_names=["excel"]
            )

            async with excel_agent:
                excel_llm = await excel_agent.attach_llm(
                    OpenAIAugmentedLLM
                )

                self.excel_result = await excel_llm.generate_str(
                    message="Generate the Excel file with the provided financial data.",
                    request_params=RequestParams(
                        model=excel_writer_model_name, 
                        temperature=0.7, 
                        max_iterations=10
                    ),
                )

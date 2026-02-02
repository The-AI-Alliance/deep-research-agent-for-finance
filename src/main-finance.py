#!/usr/bin/env python
"""
Deep Orchestrator Finance Research Example

This example demonstrates the Deep Orchestrator (AdaptiveOrchestrator) for financial research with:
- Dynamic agent creation and caching
- Knowledge extraction and accumulation
- Budget tracking (tokens, cost, time)
- Task queue management with dependencies
- Policy-driven execution control
- Full state visibility throughout execution
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

from mcp_agent.workflows.deep_orchestrator.config import (
    DeepOrchestratorConfig,
    ExecutionConfig,
    BudgetConfig,
)

from common.deep_search import DeepSearch, BaseTask, GenerateTask, AgentTask
from common.path_utils import resolve_path
from ux import Display

from finance_deep_search.ux.rich import RichDisplay
from finance_deep_search.ux.markdown import MarkdownDisplay

if __name__ == "__main__":

    def_app_name = "finance_deep_research"
    def_reporting_currency = "USD"
    def_output_path = "./output"
    def_prompts_dir = "./prompts"
    def_financial_research_agent_prompt_file = "financial_research_agent.md"
    def_excel_writer_agent_prompt_file = "excel_writer_agent.md"

    parser = argparse.ArgumentParser(
        description="Deep Finance Research using orchestrated AI agents",
        epilog="""
Due to current limitations, you must use either OpenAI, Anthropic, or local models
served by ollama, and you have to tell us which one using the `--provider` argument,
although it defaults to 'openai'. The same provider must be used for BOTH the 
orchestrator and excel writer models, so specify them accordingly. The default is 'openai',
which works for both OpenAI and Ollama, but you currently have to edit mcp_agent.config.yaml
to use the correct settings!
"""
    )
    parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker symbol, e.g., META, AAPL, GOOGL, etc."
    )
    parser.add_argument(
        "--company-name",
        required=True,
        help="Full company name"
    )    
    parser.add_argument(
        "--reporting-currency",
        default=def_reporting_currency,
        help=f"The currency used by the company for financial reporting. (Default:{def_reporting_currency})"
    )    
    parser.add_argument(
        "--output-path",
        default=def_output_path,
        help=f"Path where Excel and other output files will be saved. (Default: {def_output_path})"
    )
    parser.add_argument(
        "--prompts-dir",
        default=def_prompts_dir,
        help=f"Path to the directory where prompt files are located. (Default: {def_prompts_dir})"
    )
    relative = "If the path doesn't contain a directory specification, then the file will be searched for in the value of '--prompts-dir'."
    parser.add_argument(
        "--financial-research-prompt-path",
        default=def_financial_research_agent_prompt_file,
        help=f"Path where the main research agent prompt file is located. (Default: {def_financial_research_agent_prompt_file}) {relative}"
    )
    parser.add_argument(
        "--excel-writer-agent-prompt-path",
        default=def_excel_writer_agent_prompt_file,
        help=f"Path where the Excel writer agent prompt file is located. (Default: {def_excel_writer_agent_prompt_file}) {relative}"
    )
    parser.add_argument(
        "--orchestrator-model",
        default="gpt-4o",
        help="The model used the orchestrator agent (default: gpt-4o); it should be very capable."
    )
    parser.add_argument(
        "--excel-writer-model",
        default="o4-mini",
        help="The model used for writing results to Excel (default: o4-mini); a less powerful model is sufficient."
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "ollama"], 
        default="openai",
        help="The inference provider. Where is the model served? See the note at the bottom of this help. (Default: openai)"
    )
    parser.add_argument(
        "-u", "--ux",
        choices=["rich", "markdown"],
        default="rich",
        help="The 'UX' to use. Use 'rich' (the default) for a rich console UX and 'markdown' for streaming updates in markdown syntax."
    )
    parser.add_argument(
        '--short-run',
        action='store_true',
        help="Sets some low maximum thresholds to create a shorter run. This is primarily a debugging tool, as lower iterations, for example, means lower quality results."
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print some extra output. Useful for some testing and debugging scenarios."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create configuration for the Deep Orchestrator
    # To add additional servers, define them in mcp_agent.config.yaml,
    # then add them by name the list passed for `available_servers`.
    # See the project README for details.
    config: DeepOrchestratorConfig = DeepSearch.make_default_config(
        args.short_run,
        "DeepFinancialResearcher",
        ["excel_writer", "fetch", "filesystem", "financial-datasets", "yfmcp"])
    
    max_iterations = 2 if args.short_run else 10

    variables = {
        "ticker": args.ticker,
        "company_name": args.company_name,
        "reporting_currency": args.reporting_currency,
        "temperature": 0.7, 
        "max_iterations": max_iterations,
        "short_run": args.short_run,
        "verbose": args.verbose,
        "ux": args.ux,
        "provider": args.provider,
        "output_path": output_dir,
        "output_spreadsheet_path": f"{args.output_path}/financials_{args.ticker}.xlsx",
    }

    prompts_dir_path = Path(args.prompts_dir)
    financial_research_prompt_path = resolve_path(args.financial_research_prompt_path, prompts_dir_path)
    excel_writer_agent_prompt_path = resolve_path(args.excel_writer_agent_prompt_path, prompts_dir_path)

    tasks = [
        GenerateTask(
            name="financial_research",
            model_name=args.orchestrator_model,
            prompt_path=financial_research_prompt_path,
            output_path=Path(args.output_path)),
        AgentTask(
            name="excel_writer",
            model_name=args.excel_writer_model,
            prompt_path=excel_writer_agent_prompt_path,
            generate_prompt="Generate the Excel file with the provided financial data.",
            output_path=Path(args.output_path)),
    ]

    ux_title = "Deep Research Agent for Finance"
    if args.ux == "rich":
        ux_update_iteration_frequency_secs = 0.5
        make_display = lambda ds, vars: RichDisplay.make(
            ux_title, ds, ux_update_iteration_frequency_secs, vars)
    elif args.ux == "markdown":
        variables['print_on_update'] = True  # TODO: make this user configurable.
        ux_update_iteration_frequency_secs = 10
        make_display = lambda ds, vars: MarkdownDisplay.make(
            ux_title, ds, ux_update_iteration_frequency_secs, vars)
    else:
        # The "ux" argument definition should prevent unexpected values, 
        # but just in case...
        raise ValueError(f"Unexpected value for 'ux': {args.ux}")

    deep_search = DeepSearch(
        app_name=def_app_name,
        make_display=make_display,
        config=config,
        provider=args.provider,
        tasks=tasks,
        output_path=args.output_path,
        variables=variables)
    asyncio.run(deep_search.run())

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

from deep_search import DeepSearch

if __name__ == "__main__":

    def_app_name = "finance_deep_research"
    def_reporting_currency = "USD"
    def_output_path = "./output"
    def_prompts_path = "./prompts"
    def_financial_research_agent_prompt_file = "financial_research_agent.md"
    def_excel_writer_agent_prompt_file = "excel_writer_agent.md"

    parser = argparse.ArgumentParser(
        description="Deep Finance Research using orchestrated AI agents"
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
        help=f"Path where Excel output files will be saved. (Default: {def_output_path})"
    )
    parser.add_argument(
        "--prompts-path",
        default=def_prompts_path,
        help=f"Path where prompt files are located. (Default: {def_prompts_path})"
    )
    relative = "If the path doesn't contain a directory specification, then the file will be searched for in the value of '--prompts-path'."
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
        "-u", "--ux",
        choices=["rich", "markdown"],
        default="rich",
        help="The 'UX' to use. Use 'rich' (the default) for a rich console UX and 'markdown' for streaming updates in markdown syntax."
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print some extra output. Useful for some testing and debugging scenarios."
    )
    parser.add_argument(
        "-n", "--noop",
        action='store_true',
        help="Just print some things that would be done, but don't actually do them - useful for debugging."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    output_spreadsheet_path=f"{args.output_path}/financials_{args.ticker}.xlsx",

    if args.verbose:
        pwd = os.path.dirname(os.path.realpath(__file__))
        print(f"""
{def_app_name}: (this script: {sys.argv[0]})
  Company:
    Ticker:              {args.ticker}
    Company:             {args.company_name}
    Reporting Currency:  {args.reporting_currency}
  Models:
    Orchestrator:        {args.orchestrator_model}
    Excel Writer:        {args.excel_writer_model}
  Prompts:
    Path:                {args.prompts_path}
    Financial Research prompt file: 
                         {args.financial_research_prompt_path}
    Excel writer prompt file:
                         {args.excel_writer_agent_prompt_path}
  UX:                    {args.ux}
  Output path:           {args.output_path}
    For spreadsheet:     {output_spreadsheet_path}
  Current working dir:   {pwd}
  Verbose?               {args.verbose}
  No op?                 {args.noop}
""")
        # Just to give the user time to see the above before the UX starts.
        time.sleep(2.0)  

    # Create configuration for the Deep Orchestrator
    config = DeepOrchestratorConfig(
        name="DeepFinancialResearcher",
        available_servers=["fetch", "filesystem", "yfmcp", "financial-datasets"],
        execution=ExecutionConfig(
            max_iterations=25,
            max_replans=2,
            max_task_retries=5,
            enable_parallel=True,
            enable_filesystem=True,
        ),
        budget=BudgetConfig(
            max_tokens=100000,
            max_cost=1.00,
            max_time_minutes=10,
        ),
    )

    deep_search = DeepSearch(
        app_name = def_app_name,
        config = config,
        ticker = args.ticker,
        company_name = args.company_name,
        reporting_currency = args.reporting_currency,
        orchestrator_model_name = args.orchestrator_model,
        excel_writer_model_name = args.excel_writer_model,
        prompts_path = args.prompts_path,
        financial_research_prompt_path = args.financial_research_prompt_path,
        excel_writer_agent_prompt_path = args.excel_writer_agent_prompt_path,
        output_path = args.output_path,
        output_spreadsheet_path = output_spreadsheet_path,
        verbose = args.verbose,
        noop = args.noop
    )

    # Run the example
    if args.ux == "rich":
        from ux.rich import rich_main
        asyncio.run(rich_main(args, config, deep_search))
    elif args.ux == "markdown":
        from ux.markdown import markdown_main
        asyncio.run(markdown_main(args, config, deep_search))
    else:
        # The "ux" argument definition should prevent unexpected values, 
        # but just in case...
        raise ValueError(f"Unknown value for 'ux': {args.ux}")

    print(f"\nFinished: See output files under {args.output_path}, e.g., the spreadsheet should be: {output_spreadsheet_path}")


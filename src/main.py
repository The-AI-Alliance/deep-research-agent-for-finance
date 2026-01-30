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

from finance_deep_search.deep_search import DeepSearch
from finance_deep_search.string_utils import truncate

async def do_main(deep_search: DeepSearch):
    mcp_app = await deep_search.setup()

    # Run the example
    display  = None
    run_live = None
    update_iteration_time = 1.0
    if args.ux == "rich":
        from finance_deep_search.ux.rich import rich_init, rich_run_live
        display = rich_init("Deep Research Agent for Finance", deep_search, args)
        run_live = rich_run_live
        update_iteration_time = 0.5
    elif args.ux == "markdown":
        from finance_deep_search.ux.markdown import markdown_init, markdown_run_live
        display = markdown_init("Deep Research Agent for Finance", deep_search, args)
        run_live = markdown_run_live
        update_iteration_time = 10.0  # Update the Markdown "display" far less frequently.
    else:
        # The "ux" argument definition should prevent unexpected values, 
        # but just in case...
        raise ValueError(f"Unknown value for 'ux': {args.ux}")

    async def update_loop():
        while True:
            try:
                display.update()
                await asyncio.sleep(update_iteration_time)
            except Exception as e:
                mcp_app.logger.error(f"Display update error: {e}")
                break

    async def do_work(display):
        # Start update loop
        update_task = asyncio.create_task(update_loop())

        results = {}
        try:
            results = await deep_search.run()
        finally:
            # Final update
            display.update()
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass

        # Show the results
        research_results = results.get('research')
        if research_results:
            mcp_app.logger.info(truncate(research_results, 2000, '...'))
        else:
            mcp_app.logger.error("No research results!!")

        excel_results = results.get('excel')
        if excel_results:
            mcp_app.logger.info(truncate(excel_results, 2000, '...'))
        else:
            mcp_app.logger.error("No Excel results!!")

        display.report_results(research_results, excel_results)

        await display.final_data_update()

        final_messages = [
            "\n",
            f"Finished: See output files under {args.output_path}.",
            f"For example, the spreadsheet should be: {output_spreadsheet_path}",
        ]
        display.show_final_messages(final_messages)

    await run_live(display, do_work)

if __name__ == "__main__":

    def_app_name = "finance_deep_research"
    def_reporting_currency = "USD"
    def_output_path = "./output"
    def_prompts_path = "./prompts"
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
    Provider:            {args.provider}
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
  Short run?             {args.short_run}
  Verbose?               {args.verbose}
""")
        # Just to give the user time to see the above before the UX starts.
        time.sleep(2.0)  

    # Create configuration for the Deep Orchestrator
    if args.short_run:
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
        name="DeepFinancialResearcher",
        available_servers=["fetch", "filesystem", "yfmcp", "financial-datasets"],
        execution=execution_config,
        budget=budget_config,
    )

    deep_search = DeepSearch(
        app_name = def_app_name,
        config = config,
        ticker = args.ticker,
        company_name = args.company_name,
        reporting_currency = args.reporting_currency,
        orchestrator_model_name = args.orchestrator_model,
        excel_writer_model_name = args.excel_writer_model,
        provider = args.provider,
        prompts_path = args.prompts_path,
        financial_research_prompt_path = args.financial_research_prompt_path,
        excel_writer_agent_prompt_path = args.excel_writer_agent_prompt_path,
        output_path = args.output_path,
        output_spreadsheet_path = output_spreadsheet_path,
        short_run = args.short_run,
        verbose = args.verbose,
    )

    asyncio.run(do_main(deep_search))


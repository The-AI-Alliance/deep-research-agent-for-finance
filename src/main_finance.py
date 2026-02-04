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
from datetime import datetime
from pathlib import Path
from typing import Callable

from mcp_agent.workflows.deep_orchestrator.config import (
    DeepOrchestratorConfig,
    ExecutionConfig,
    BudgetConfig,
)

from common.deep_search import DeepSearch, BaseTask, GenerateTask, AgentTask
from common.main_utils import (
    make_parser,
    add_arg_output_dir,
    add_arg_markdown_report_path,
    add_arg_prompts_dir,
    add_arg_research_model,
    add_arg_provider,
    add_arg_temperature,
    add_arg_max_iterations,
    add_arg_ux,
    add_arg_short_run,
    add_arg_verbose,
    process_args,
    determine_display,
    read_relative_to,
    written_relative_to,
    var_start_time,
    var_output_dir_path,
    var_prompts_dir_path,
    var_research_report_path,
    var_provider,
    var_research_model,
    var_research_model,
    var_ux,
    vars_verbose_only,
)
from common.path_utils import resolve_path
from common.variables import Variable
from ux import Display

if __name__ == "__main__":

    def_app_name = "finance_deep_research"
    def_reporting_currency = "USD"
    def_output_dir = "./output"
    def_prompts_dir = "./prompts"
    def_financial_research_agent_prompt_file = "financial_research_agent.md"
    def_excel_writer_agent_prompt_file = "excel_writer_agent.md"
    def_markdown_report_path = 'research_report.md'
    def_excel_spreadsheet_path = 'financials.xlsx'
    def_provider = 'openai'
    def_research_model = 'gpt-4o'
    def_excel_writer_model = 'o4-mini'
    def_ux = 'rich'
    def_temperature = 0.7
    def_max_iterations = 10

    parser = make_parser("Finance Deep Research using orchestrated AI agents")
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
    add_arg_output_dir(parser, def_output_dir)
    add_arg_markdown_report_path(parser, def_markdown_report_path)
    parser.add_argument(
        "--output-spreadsheet",
        default=def_excel_spreadsheet_path,
        help=f"Path where the Excel spreadsheet is written. (Default: {def_excel_spreadsheet_path}) {written_relative_to('output-dir')}"
    )
    add_arg_prompts_dir(parser, def_prompts_dir)
    parser.add_argument(
        "--financial-research-prompt-path",
        default=def_financial_research_agent_prompt_file,
        help=f"Path where the main research agent prompt file is located. (Default: {def_financial_research_agent_prompt_file}) {read_relative_to('prompts-dir')}"
    )
    parser.add_argument(
        "--excel-writer-agent-prompt-path",
        default=def_excel_writer_agent_prompt_file,
        help=f"Path where the Excel writer agent prompt file is located. (Default: {def_excel_writer_agent_prompt_file}) {read_relative_to('prompts-dir')}"
    )
    add_arg_research_model(parser, def_research_model)
    parser.add_argument(
        "--excel-writer-model",
        default=def_excel_writer_model,
        help=f"The model used for writing results to Excel (default: {def_excel_writer_model}); a less powerful model is sufficient."
    )
    add_arg_provider(parser, def_provider)
    add_arg_ux(parser, def_ux)
    add_arg_temperature(parser, def_temperature)
    add_arg_max_iterations(parser, def_max_iterations)
    add_arg_short_run(parser)
    add_arg_verbose(parser)

    args, processed_args = process_args(parser)
    
    # Change to app directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create configuration for the Deep Orchestrator
    # To add additional servers, define them in mcp_agent.config.yaml,
    # then add them by name the list passed for `available_servers`.
    # See the project README for details.
    config: DeepOrchestratorConfig = DeepSearch.make_default_config(
        args.short_run,
        "FinancialDeepResearcher",
        ["excel_writer", "fetch", "filesystem", "financial-datasets", "yfmcp"])

    output_dir_path = Path(args.output_dir)
    markdown_report_path = resolve_path(args.markdown_report, output_dir_path)
    output_spreadsheet_path = resolve_path(args.output_spreadsheet, output_dir_path)
    
    prompts_dir_path = Path(args.prompts_dir)
    financial_research_prompt_path = resolve_path(args.financial_research_prompt_path, prompts_dir_path)
    excel_writer_agent_prompt_path = resolve_path(args.excel_writer_agent_prompt_path, prompts_dir_path)


    # The variables dict contains values used by the app components, labels 
    # for display purposes and a formatter for rendering the value, either a dict, 
    # a function for rendering, or `None`, for which `str(x)` will be used. 
    # (For a dict, if the item isn't found, `str(x)` will be used.)
    # The entries also indicate which of the variables to render (e.g., more
    # of them when verbose output is desired) and the order of presentation.
    variables_list = [
        var_start_time(processed_args['start_time']),
        Variable("ticker",                   args.ticker),
        Variable("company_name",             args.company_name),
        Variable("reporting_currency",       args.reporting_currency),
        Variable("units",                    f"{args.reporting_currency} millions"),
        var_output_dir_path(output_dir_path),
        var_research_report_path(markdown_report_path),
        Variable("output_spreadsheet_path",  output_spreadsheet_path, formatter=Variable.file_url_formatter),
        var_provider(args.provider),
        var_research_model(args.research_model),
        Variable("excel_writer_model",       args.excel_writer_model, formatter=Variable.code_formatter),
        var_prompts_dir_path(prompts_dir_path),
        Variable("financial_research_prompt_path", 
                                             financial_research_prompt_path, formatter=Variable.file_url_formatter),
        Variable("excel_writer_agent_prompt_path", 
                                             excel_writer_agent_prompt_path, formatter=Variable.file_url_formatter),
        var_ux(args.ux),
    ]
    variables_list.extend(vars_verbose_only(args, processed_args, config))

    variables = dict([(v.key, v) for v in variables_list])

    tasks = [
        GenerateTask(
            name="financial_research",
            title="📊 Financial Research Result",
            model_name=args.research_model,
            prompt_template_path=financial_research_prompt_path,
            output_dir_path=output_dir_path,
            temperature=processed_args['temperature'], 
            max_iterations=processed_args['max_iterations']),
        AgentTask(
            name="excel_writer",
            title="📈 Excel Creation Result",
            model_name=args.excel_writer_model,
            prompt_template_path=excel_writer_agent_prompt_path,
            output_dir_path=output_dir_path,
            generate_prompt="Generate the Excel file with the provided financial data.",
            temperature=processed_args['temperature'], 
            max_iterations=processed_args['max_iterations']),
    ]

    ux_title = "Deep Research Agent for Finance"

    make_display = determine_display(args.ux, ux_title)

    deep_search = DeepSearch(
        app_name=def_app_name,
        make_display=make_display,
        config=config,
        provider=args.provider,
        tasks=tasks,
        output_dir_path=output_dir_path,
        variables=variables)
    asyncio.run(deep_search.run())

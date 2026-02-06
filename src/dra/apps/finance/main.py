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

print(f"path: {Path(__file__).resolve().parent}")

from dra.common.deep_search import DeepSearch
from dra.common.tasks import BaseTask, GenerateTask, AgentTask
from dra.common.utils.main import (
    make_parser,
    add_arg_output_dir,
    add_arg_markdown_report_path,
    add_arg_markdown_yaml_header_template_path,
    add_arg_templates_dir,
    add_arg_research_model,
    add_arg_provider,
    add_arg_temperature,
    add_arg_max_iterations,
    add_arg_max_tokens,
    add_arg_max_cost_dollars,
    add_arg_max_time_minutes,
    add_arg_short_run,
    add_arg_verbose,
    common_variables,
    process_args,
    read_relative_to,
    written_relative_to,
    only_verbose_common_vars,
    only_verbose,
)
from dra.common.utils.paths import resolve_path, resolve_and_require_path
from dra.common.variables import Variable
from dra.ux.display import Display

if __name__ == "__main__":

    def_app_name = "finance_deep_research"
    def_reporting_currency = "USD"
    def_output_dir = "./output"
    def_templates_dir = "./templates"
    def_financial_research_agent_prompt_file = "financial_research_agent.md"
    def_excel_writer_agent_prompt_file = "excel_writer_agent.md"
    def_markdown_report_path = 'research_report.md'
    def_markdown_yaml_header_template_path = None
    def_excel_spreadsheet_path = 'financials.xlsx'
    def_provider = 'openai'
    def_research_model = 'gpt-4o'
    def_excel_writer_model = 'o4-mini'
    def_temperature = 0.7
    def_max_iterations = 25
    def_max_tokens = 500000
    def_max_cost_dollars = 2.0
    def_max_time_minutes = 15

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
    add_arg_templates_dir(parser, def_templates_dir)
    parser.add_argument(
        "--financial-research-prompt-path",
        default=def_financial_research_agent_prompt_file,
        help=f"Path where the main research agent prompt file is located. (Default: {def_financial_research_agent_prompt_file}) {read_relative_to('templates-dir')}"
    )
    parser.add_argument(
        "--excel-writer-agent-prompt-path",
        default=def_excel_writer_agent_prompt_file,
        help=f"Path where the Excel writer agent prompt file is located. (Default: {def_excel_writer_agent_prompt_file}) {read_relative_to('templates-dir')}"
    )
    add_arg_markdown_yaml_header_template_path(parser, def_markdown_yaml_header_template_path)
    add_arg_research_model(parser, def_research_model)
    parser.add_argument(
        "--excel-writer-model",
        default=def_excel_writer_model,
        help=f"The model used for writing results to Excel (default: {def_excel_writer_model}); a less powerful model is sufficient."
    )
    add_arg_provider(parser, def_provider)
    add_arg_temperature(parser, def_temperature)
    add_arg_max_iterations(parser, def_max_iterations)
    add_arg_max_tokens(parser, def_max_tokens)
    add_arg_max_cost_dollars(parser, def_max_cost_dollars)
    add_arg_max_time_minutes(parser, def_max_time_minutes)
    add_arg_short_run(parser)
    add_arg_verbose(parser)

    args, processed_args = process_args(parser)
    
    # Change to app directory
    # os.chdir(os.path.dirname(os.path.abspath(__file__)))

    output_dir_path = process_args['output_dir_path']
    output_spreadsheet_path = resolve_path(args.output_spreadsheet, output_dir_path)
    
    templates_dir_path = process_args['templates_dir_path']
    # These must exist:
    financial_research_prompt_path = resolve_and_require_path(args.financial_research_prompt_path, templates_dir_path)
    excel_writer_agent_prompt_path = resolve_and_require_path(args.excel_writer_agent_prompt_path, templates_dir_path)

    # The variables dict contains values used by the app components, labels 
    # for display purposes and a format for knowing how to render the value.
    # Start with values we want to see at the top:
    variables_list = [
        Variable("start_time",                     processed_args['start_time']),
        Variable("ticker",                         args.ticker),
        Variable("company_name",                   args.company_name),
        Variable("reporting_currency",             args.reporting_currency),
        Variable("units",                          f"{args.reporting_currency} millions"),
    ]
    # Add common values across apps:
    variables_list.extend(common_variables(args, processed_args, output_dir_path, templates_dir_path))
    
    # Finish with the remaining custom variables for this app and "verbose" variables:
    variables_list.extend([
        Variable("excel_writer_model",             args.excel_writer_model, kind='code'),
        Variable("output_spreadsheet_path",        output_spreadsheet_path, kind='file'),
        Variable("financial_research_prompt_path", financial_research_prompt_path, kind='file'),
        Variable("excel_writer_agent_prompt_path", excel_writer_agent_prompt_path, kind='file'),
    ])
    variables_list.extend(only_verbose_common_vars(args, processed_args))
    variables_list['ux_title'] = "Deep Research Agent for Finance"

    variables = dict([(v.key, v) for v in variables_list])

    tasks = [
        GenerateTask(
            name="financial_research",
            title="📊 Financial Research Result",
            model_name=args.research_model,
            prompt_template_path=financial_research_prompt_path,
            output_dir_path=output_dir_path,
            properties=variables),
        AgentTask(
            name="excel_writer",
            title="📈 Excel Creation Result",
            model_name=args.excel_writer_model,
            prompt_template_path=excel_writer_agent_prompt_path,
            output_dir_path=output_dir_path,
            generate_prompt="Generate the Excel file with the provided financial data.",
            properties=variables),
    ]

    # Create configuration for the Deep Orchestrator
    # To add additional servers, define them in mcp_agent.config.yaml,
    # then add them by name the list passed for `available_servers`.
    # See the project README for details.
    config: DeepOrchestratorConfig = DeepSearch.make_default_config(
        args.short_run,
        "FinancialDeepResearcher",
        ["excel_writer", "fetch", "filesystem", "financial-datasets", "yfmcp"],
        variables)

    variables["config"] = Variable("config", config, label="Configuration", kind=only_verbose(args))

    observers = process_args['observers']    
    display = process_args['display']
    
    deep_search = DeepSearch(
        app_name=def_app_name,
        provider=args.provider,
        config=config,
        tasks=tasks,
        output_dir_path=output_dir_path,
        display=display,
        observers=observers,
        variables=variables)

    asyncio.run(deep_search.run())

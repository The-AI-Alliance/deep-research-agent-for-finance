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

import asyncio, sys
from pathlib import Path
from dra.common.observer import Observer
from dra.common.tasks import BaseTask, GenerateTask, AgentTask
from dra.common.utils.io import UserPrompts
from dra.common.utils.main import ParserUtil, Runner
from dra.common.utils.paths import resolve_path, resolve_and_require_path
from dra.common.variables import Variable
from dra.ux.display import Display

def get_server_list() -> list[str]:
    """Define the list of tools and services to use for this app."""
    return [
        "excel_writer",
        "fetch",
        "filesystem",
        "financial-datasets",
        "yfmcp",
    ]

def get_extra_observers() -> dict[str, Observer]:
    """
    Define any "extra" observers you want, e.g., for additional logging or tracing.
    To avoid subtle bugs, it is disallowed to add a new observer with the same key
    as an existing observer. Hence, the `Runner` object used below will verify
    there are no "key collisions".
    """
    return {} # none by default

class FinanceParseUtil(ParserUtil):
    def __init__(self, which_app: str, app_name: str, ux_title: str, description: str):
        super().__init__(which_app, app_name, ux_title, description)

    def _do_prompt_for_missing_args(self, up: UserPrompts) -> dict[str, any]:
        """Prompt the user for the company ticker and name, if necessary."""
        ticker = self.args.ticker
        if not ticker or not ticker.strip():
            ticker = up.read_one_line_input("Input the company ticker symbol")

        company_name = self.args.company_name
        if not company_name or not company_name.strip():
            company_name = up.read_one_line_input("Input the company name")

        return {
            'ticker': ticker,
            'company_name': company_name
        }

def define_cli_arguments() -> ParserUtil:
    """
    Start by defining default values for our custom CLI arguments, 
    followed by the names, UX title, etc. for this app.

    Returns:
        ParserUtil:        A utility that handles CLI arguments and common processing steps for them.
    """

    def_reporting_currency = "USD"
    def_financial_research_agent_prompt_file = "financial_research_agent.md"
    def_excel_writer_agent_prompt_file = "excel_writer_agent.md"
    def_excel_spreadsheet_path = 'financials.xlsx'
    def_excel_writer_model = 'o4-mini'
    
    which_app='finance'
    app_name = "financial_deep_research"
    ux_title='Financial Deep Research Agent'
    description = "Financial Deep Research using orchestrated AI agents"
    parser_util = FinanceParseUtil(which_app, app_name, ux_title, description)

    # Define the CLI arguments. It is best to put required arguments first.

    parser_util.parser.add_argument(
        "--ticker",
        help="Stock ticker symbol, e.g., META, AAPL, GOOGL, etc. If not provided on the command line, you will be prompted for it."
    )
    parser_util.parser.add_argument(
        "--company-name",
        help="Full company name. If not provided on the command line, you will be prompted for it."
    )    
    parser_util.parser.add_argument(
        "--reporting-currency",
        default=def_reporting_currency,
        help=f"The currency used by the company for financial reporting. (Default: {def_reporting_currency})"
    )    
    parser_util.add_arg_markdown_report_path()
    parser_util.add_arg_markdown_research_report_title()
    parser_util.add_arg_output_dir()
    parser_util.parser.add_argument(
        "--output-spreadsheet",
        default=def_excel_spreadsheet_path,
        help=f"Path where the Excel spreadsheet is written. (Default: {def_excel_spreadsheet_path}) {parser_util.written_relative_to('output-dir')}"
    )
    parser_util.add_arg_templates_dir()
    parser_util.parser.add_argument(
        "--financial-research-prompt-path",
        default=def_financial_research_agent_prompt_file,
        help=f"Path where the main research agent prompt file is located. (Default: {def_financial_research_agent_prompt_file}) {parser_util.read_relative_from('templates-dir')}"
    )
    parser_util.parser.add_argument(
        "--excel-writer-agent-prompt-path",
        default=def_excel_writer_agent_prompt_file,
        help=f"Path where the Excel writer agent prompt file is located. (Default: {def_excel_writer_agent_prompt_file}) {parser_util.read_relative_from('templates-dir')}"
    )
    parser_util.add_arg_markdown_yaml_header_template_path()
    parser_util.add_arg_research_model()
    parser_util.parser.add_argument(
        "--excel-writer-model",
        default=def_excel_writer_model,
        help=f"The model used for writing results to Excel (default: {def_excel_writer_model}); a less powerful model is sufficient."
    )
    parser_util.add_arg_provider()
    parser_util.add_arg_mcp_agent_config_path()
    parser_util.add_arg_temperature()
    parser_util.add_arg_max_iterations()
    parser_util.add_arg_max_tokens()
    parser_util.add_arg_max_cost_dollars()
    parser_util.add_arg_max_time_minutes()
    parser_util.add_arg_short_run()
    parser_util.add_arg_verbose()
    
    return parser_util

def process_cli_arguments(parser_util: ParserUtil):
    """
    Process the actual supplied arguments, resolve the common input and output paths
    like for `--markdown-report` and `--markdown-yaml-header`, etc. (See the discussion
    in the project README.md.)
    """

    parser_util.process_args()

    # Custom paths for this app, such as the output spreadsheet to write.
    # For example, the help for this option (and most output options) tells the user
    # that if the argument doesn't have a path prefix, we will write to the location
    # specified by `--output-dir`. We call `resolve_path` to handle this. (This is done
    # for you in `parser_util.process_args()` for common arguments like `--markdown-report`
    # Obviously an 
    # output file isn't expected to exist yet, so `resolve_and_require_path` isn't called!

    output_dir_path = parser_util.processed_args['output_dir_path']
    output_spreadsheet_path = resolve_path(parser_util.args.output_spreadsheet, output_dir_path)
    
    # For example, the help for `--markdown-yaml-header`
    # tells the user that if the argument doesn't have a path prefix, we will read
    # the file from the `template_path` location. For input files, we will raise an
    # exception if it doesn't exist. We call `resolve_and_require_path` to perform
    # this path resolution and ensure the file exists.
    # Similarly, output files specified, such as `--markdown-report`, will be written
    # to the `output_dir_path` location, if the path provided doesn't contain a
    # directory prefix. Here we call `resolve_path` to handle this. Obviously an 
    # output file isn't expected to exist yet, so `resolve_and_require_path` isn't called!

    # Template files (for the prompts here) work similarly, but because these
    # are input paths, we call `resolve_and_require_path` to ensure they exist. 
    # If not, an exception is raised.
    templates_dir_path = parser_util.processed_args['templates_dir_path']
    # These must exist:
    financial_research_prompt_path = resolve_and_require_path(
        parser_util.args.financial_research_prompt_path, templates_dir_path)
    excel_writer_agent_prompt_path = resolve_and_require_path(
        parser_util.args.excel_writer_agent_prompt_path, templates_dir_path)

    parser_util.processed_args.update({
        'output_spreadsheet_path':        output_spreadsheet_path, 
        'financial_research_prompt_path': financial_research_prompt_path,
        'excel_writer_agent_prompt_path': excel_writer_agent_prompt_path,
    })

def create_variables(parser_util: ParserUtil) -> dict[str, Variable]:
    """
    The variables dict contains values used throughout the app, including labels 
    for display purposes and a format feature for rendering the values as plain text,
    Markdown-appropriate (e.g., `foo` for code), etc. The returned `Variable` dictionary
    is used more or less like typical Python function `**kvs`.
    Because the variables are also used for display purposes, we declare them somewhat in
    the order of most interest to the user, starting with application-specific definitions.

    Args:
        parser_util (ParserUtil):  A utility that handles CLI arguments and common processing steps for them.

    Return:
        dict[str, Variable]:       A dictionary of `Variable`s used throughout the app.
    """
    variables_list = [
        Variable("start_time",           parser_util.processed_args["start_time"]),
        Variable("ticker",               parser_util.processed_args["ticker"]),
        Variable("company_name",         parser_util.processed_args["company_name"]),
        Variable("reporting_currency",   parser_util.args.reporting_currency),
        Variable("units",                f"{parser_util.args.reporting_currency} millions"),
    ]

    # Add common values across apps:
    variables_list.extend(parser_util.common_variables())
    
    # Finish with the remaining custom variables for this app and "verbose" variables:
    variables_list.extend([
        Variable("excel_writer_model",             parser_util.args.excel_writer_model, kind='code'),
        Variable("output_spreadsheet_path",        parser_util.processed_args["output_spreadsheet_path"], kind='file'),
        Variable("financial_research_prompt_path", parser_util.processed_args["financial_research_prompt_path"], kind='file'),
        Variable("excel_writer_agent_prompt_path", parser_util.processed_args["excel_writer_agent_prompt_path"], kind='file'),
    ])
    variables_list.extend(parser_util.only_verbose_common_vars())

    return dict([(v.key, v) for v in variables_list])

def make_tasks(parser_util: ParserUtil, variables: dict[str, Variable]) -> list[BaseTask]:
    """
    Create the tasks for this research agent. All applications will start with a 
    `GenerateTask` to drive the `mcp-agent` "Deep Orchestrator" that invokes the tools
    and MCP services (discussed below) to do the basic research, aggregate the results 
    and generate a report at the end.
    Additional `AgentTask`s and `GenerateTask`s might be used for additional processing.
    In the finance app, an `AgentTask` is used to generate an Excel spreadsheet with the 
    results.

    Args:
        parser_util (ParserUtil):         A utility that handles CLI arguments and common processing steps for them.
        variables (dict[str, Variable]):  A dictionary of `Variable`s used throughout the app.

    Return:
        list[BaseTask]:                   A list of the tasks to do.
    """

    tasks = [
        GenerateTask(
            name="financial_research",
            title="📊 Financial Research Result",
            model_name=parser_util.args.research_model,
            prompt_template_path=variables['financial_research_prompt_path'].value,
            output_dir_path=variables['output_dir_path'].value,
            properties=variables),
        AgentTask(
            name="excel_writer",
            title="📈 Excel Creation Result",
            model_name=parser_util.args.excel_writer_model,
            prompt_template_path=variables['excel_writer_agent_prompt_path'].value,
            output_dir_path=variables['output_dir_path'].value,
            generate_prompt="Generate the Excel file with the provided financial data.",
            properties=variables),
    ]
    return tasks

if __name__ == "__main__":
    parser_util = define_cli_arguments()
    process_cli_arguments(parser_util)
    variables = create_variables(parser_util)
    tasks = make_tasks(parser_util, variables)
    runner = Runner(
        tasks, get_server_list(), get_extra_observers(), parser_util, variables)
    asyncio.run(runner.run())

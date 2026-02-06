# Common utilities for the application "main" files.

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from dra.common.deep_search import DeepSearch
from dra.common.utils.paths import resolve_path, resolve_and_require_path
from dra.common.variables import Variable

from dra.ux.display import Display
from dra.ux.rich import RichDisplay
from dra.ux.markdown import MarkdownObserver

def make_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        epilog="""
Due to current limitations, you must use either OpenAI, Anthropic, or local models
served by ollama, and you have to tell us which one using the `--provider` argument,
although it defaults to 'openai'. The same provider must be used for BOTH the 
orchestrator and excel writer models, so specify them accordingly. The default is 'openai',
which works for both OpenAI and Ollama, but you currently have to edit mcp_agent.config.yaml
to use the correct settings!
"""
    )
    return parser


def relative_to(rw: str, where: str) -> str:
    return f"If the path doesn't contain a directory prefix, then the file will be {rw} in the directory given by '--{where}'."

def read_relative_to(where: str) -> str:
    return relative_to('read', where)

def written_relative_to(where: str) -> str:
    return relative_to('written', where)


def add_arg_output_dir(parser: argparse.ArgumentParser, def_output_dir: str = './output'):
    parser.add_argument(
        "--output-dir",
        default=def_output_dir,
        help=f"Path where Excel and other output files will be saved. (Default: {def_output_dir})"
    )

def add_arg_markdown_report_path(parser: argparse.ArgumentParser, def_markdown_report_path: str = 'research_report.md'):
    parser.add_argument(
        "--markdown-report",
        default=def_markdown_report_path,
        help=f"Path where a Markdown report is written. If empty, no report is generated. (Default: {def_markdown_report_path}) {written_relative_to('output-dir')}"
    )

def add_arg_templates_dir(parser: argparse.ArgumentParser, def_templates_dir: str = './templates'):
    parser.add_argument(
        "--templates-dir",
        default=def_templates_dir,
        help=f"Path to the directory where template files are located (e.g., for inference prompts). (Default: {def_templates_dir})"
    )

def add_arg_markdown_yaml_header_template_path(parser: argparse.ArgumentParser, def_markdown_yaml_header_template_path: str = None):
    parser.add_argument(
        "--markdown-yaml-header",
        default=def_markdown_yaml_header_template_path,
        help=f"Path to an optional template for a YAML header to write at the beginning of the Markdown report. Useful for publishing the report on a GitHub Pages website. Ignored if --markdown-report is empty. (Default: {def_markdown_yaml_header_template_path}) {read_relative_to('template-dir')}"
    )

def add_arg_research_model(parser: argparse.ArgumentParser, def_research_model: str = 'gpt-4o'):
    parser.add_argument(
        "--research-model",
        default=def_research_model,
        help=f"The model used the research orchestrator agent. (Default: {def_research_model}). It should be very capable."
    )

def add_arg_provider(parser: argparse.ArgumentParser, def_provider: str = 'openai'):
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic", "ollama"], 
        default=def_provider,
        help=f"The inference provider. Where is the model served? See the note at the bottom of this help. (Default: {def_provider})"
    )

def add_arg_temperature(parser: argparse.ArgumentParser, def_temperature: float = 0.7):
    parser.add_argument(
        "--temperature",
        type=float,
        default=def_temperature,
        help=f"The 'temperature' used during inference calls to models, between 0.0 and 1.0. (Default: {def_temperature})"
    )

def add_arg_max_iterations(parser: argparse.ArgumentParser, def_max_iterations: int = 10):
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=def_max_iterations,
        help=f"The maximum number of iterations for inference/analysis passes. (Default: {def_max_iterations}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 1)"
    )

def add_arg_max_tokens(parser: argparse.ArgumentParser, def_max_tokens: int = 100000):
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=def_max_tokens,
        help=f"The maximum number of tokens for inference passes. (Default: {def_max_tokens}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 10000)"
    )

def add_arg_max_cost_dollars(parser: argparse.ArgumentParser, def_max_cost_dollars: float = 1.00):
    parser.add_argument(
        "--max-cost-dollars",
        type=float,
        default=def_max_cost_dollars,
        help=f"The maximum total cost in USD allowed for inference calls. (Default: {def_max_cost_dollars}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 1.00)"
    )

def add_arg_max_time_minutes(parser: argparse.ArgumentParser, def_max_time_minutes: int = 10.0):
    parser.add_argument(
        "--max-time-minutes",
        type=int,
        default=def_max_time_minutes,
        help=f"The maximum number of time in minutes allowed for inference passes. (Default: {def_max_time_minutes}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 10)"
    )

def add_arg_short_run(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--short-run',
        action='store_true',
        help="Sets some low maximum thresholds to create a shorter run. This is primarily a debugging tool, as lower iterations, for example, means lower quality results."
    )

def add_arg_verbose(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Print some extra output. Useful for some testing and debugging scenarios."
    )
    
def process_args(parser: argparse.ArgumentParser) -> (argparse.Namespace, dict[str,any]):
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir_path = Path(args.output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    markdown_report_path = None
    if args.markdown_report:
        markdown_report_path = resolve_path(args.markdown_report, output_dir_path)

    templates_dir_path = Path(args.templates_dir)
    if not templates_dir_path.exists():
        raise ValueError(f"Prompt directory '{templates_dir_path}' doesn't exist!")

    markdown_yaml_header_path = None
    if args.markdown_yaml_header:
        markdown_yaml_header_path = resolve_and_require_path(args.markdown_yaml_header, templates_dir_path)

    temperature = args.temperature
    if args.temperature < 0.0:
        temperature = 0.0
    if args.temperature > 1.0:
        temperature = 1.0
    
    max_iterations = 1 if args.short_run else args.max_iterations
    if max_iterations < 1:
        max_iterations = 1

    max_tokens = 10000 if args.short_run else args.max_tokens
    if max_tokens < 1:
        max_tokens = 10000

    max_cost_dollars = 1.00 if args.short_run else args.max_cost_dollars
    if max_cost_dollars <= 0.0:
        max_cost_dollars = 1.00

    max_time_minutes = 10 if args.short_run else args.max_time_minutes
    if max_time_minutes < 1:
        max_time_minutes = 10

    return (args, {
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M%:%S'),
        "temperature": temperature, 
        "max_iterations": max_iterations,
        "max_tokens": max_tokens,
        "max_cost_dollars": max_cost_dollars,
        "max_time_minutes": max_time_minutes,
        "markdown_report_path": markdown_report_path,
        "yaml_header_template_path": markdown_yaml_header_path,
    })

def only_verbose(args: argparse.Namespace, formatter: str = 'str') -> str | None:
    return formatter if args.verbose else None

def common_variables(
    args: argparse.Namespace,
    processed_args: dict[str,any],
    output_dir_path: Path,
    templates_dir_path: Path) -> list[Variable]:    
    return [
        Variable("provider",                       args.provider, kind='provider'),
        Variable("research_model",                 args.research_model, kind='code'),
        Variable("templates_dir_path",             templates_dir_path, kind='file'),
        Variable("output_dir_path",                output_dir_path, kind='file'),
        Variable("research_report_path",           processed_args['markdown_report_path'], kind='file'),
        Variable("yaml_header_template_path",      processed_args['yaml_header_template_path'], kind='file'),
    ]

def only_verbose_common_vars(
    args: argparse.Namespace,
    processed_args: dict[str,any]) -> list[Variable]:
    fmt = only_verbose(args)
    return [
        Variable("verbose",           args.verbose, kind=fmt),
        Variable("short_run",         args.short_run, kind=fmt),
        Variable("temperature",       processed_args['temperature'], label="LLM Temperature", kind=fmt), 
        Variable("max_iterations",    processed_args['max_iterations'], label="LLM Max Iterations", kind=fmt),
        Variable("max_tokens",        processed_args['max_tokens'], label="LLM Max Inference Tokens", kind=fmt),
        Variable("max_cost_dollars",  processed_args['max_cost_dollars'], label="LLM Max Inference cost in USD", kind=fmt),
        Variable("max_time_minutes",  processed_args['max_time_minutes'], label="LLM Max Inference time in minutes", kind=fmt),
        Variable("update_iteration_frequency_secs", # TODO: make user configurable??
                                      1.0, label="Frequency in Seconds for Updating the Display", kind=fmt)
    ]


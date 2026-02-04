# Common utilities for the application "main" files.

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from common.deep_search import DeepSearch
from common.path_utils import resolve_and_require_path
from common.variables import Variable

from ux import Display
from ux.markdown import MarkdownDisplay
from ux.rich import RichDisplay

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
        help=f"Path where a Markdown report is written. Ignored unless --ux markdown is used. (Default: {def_markdown_report_path}) {written_relative_to('output-dir')}"
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
        help=f"Path to an optional template for a YAML header to write at the beginning of the Markdown report. Useful for publishing the report on a GitHub Pages website. Ignored unless --ux markdown is used. (Default: {def_markdown_yaml_header_template_path}) {read_relative_to('template-dir')}"
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

def add_arg_ux(parser: argparse.ArgumentParser, def_ux: str = 'rich'):
    parser.add_argument(
        "-u", "--ux",
        choices=["rich", "markdown"],
        default=def_ux,
        help=f"The 'UX' to use. Use 'rich' for a rich console UX and 'markdown' for streaming updates in markdown syntax. (Default: {def_ux})"
    )

def add_arg_short_run(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--short-run',
        action='store_true',
        help="Sets some low maximum thresholds to create a shorter run. This is primarily a debugging tool, as lower iterations, for example, means lower quality results."
    )

def add_arg_verbose(parser: argparse.ArgumentParser):
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print some extra output. Useful for some testing and debugging scenarios."
    )
    
def process_args(parser: argparse.ArgumentParser) -> (argparse.Namespace, dict[str,any]):
    args = parser.parse_args()
    
    # Configure variable formatting based on the UX:
    Variable.set_ux(args.ux)

    # Ensure output directory exists
    output_dir_path = Path(args.output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

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

    return (args, {
        'start_time': datetime.now().strftime('%Y-%m-%d %H:%M%:%S'),
        "temperature": temperature, 
        "max_iterations": max_iterations,
        "yaml_header_template_path": markdown_yaml_header_path,
    })

def determine_display(
    which_one: str,
    ux_title: str,
    **kvs) -> Callable[[DeepSearch, dict[str,(str,any)]], Display]:
    yaml = kvs.get('yaml_header_template_path', None)
    update_freq = kvs.get('update_iteration_frequency_secs', 0.0)
    if which_one == "rich":
        if update_freq <= 0.0:
            update_freq = 0.5  #default
        make_display = lambda ds, vs: RichDisplay.make(
            ux_title, ds,
            update_iteration_frequency_secs=update_freq,
            variables=vs)
    elif which_one == "markdown":
        if update_freq <= 0.0:
            update_freq = 10  #default
        make_display = lambda ds, vs: MarkdownDisplay.make(
            ux_title, ds,
            update_iteration_frequency_secs=update_freq,
            yaml_header_template=yaml,
            variables=vs)
    else:
        # The "ux" argument definition should prevent unexpected values, 
        # but just in case...
        raise ValueError(f"Unexpected value for 'ux': {args.ux}")
    return make_display

def only_verbose(args: argparse.Namespace, formatter: Callable[[any],str] = str) -> Callable[[any],str] | None:
    return formatter if args.verbose else None

def var_with_file_fmt(key: str, value: Path, label: str = None) -> Variable:
    return Variable(key, value, label=label, formatter=Variable.file_url_formatter)

def var_with_code_fmt(key: str, value: str, label: str = None) -> Variable:
    return Variable(key, value, label=label, formatter=Variable.code_formatter)

def var_with_dict_fmt(key: str, value: str, label: str = None, map: dict[str,str] = {}) -> Variable:
    return Variable(key, value, label=label, formatter=map)

def var_start_time(time: str) -> Variable:
    return Variable("start_time", time)

def var_output_dir_path(path: Path) -> Variable:
    return var_with_file_fmt("output_dir_path", path)

def var_templates_dir_path(path: Path) -> Variable:
    return var_with_file_fmt("templates_dir_path", path)

def var_research_report_path(path: Path) -> Variable:
    return var_with_file_fmt("research_report_path", path)

def var_provider(provider: str) -> Variable:
    return var_with_dict_fmt("provider", provider, map=Variable.provider_names)

def var_research_model(model: str) -> Variable:
    return var_with_code_fmt("var_research_model", model)

def var_research_model(model: str) -> Variable:
    return var_with_code_fmt("var_research_model", model)

def var_ux(ux: str) -> Variable:
    return var_with_dict_fmt("ux", ux, label="UX", map=Variable.ux_names)

def vars_verbose_only(
    args: argparse.Namespace,
    processed_args: dict[str,any],
    config: any) -> list[Variable]:
    return [
        Variable("verbose",         args.verbose, formatter=only_verbose(args)),
        Variable("short_run",       args.short_run, formatter=only_verbose(args)),
        Variable("temperature",     processed_args['temperature'], label="LLM Temperature", formatter=only_verbose(args)), 
        Variable("max_iterations",  processed_args['max_iterations'], label="LLM Max Iterations", formatter=only_verbose(args)),
        # Only used for Markdown UX. TODO: make this user configurable.
        Variable('print_on_update', False, formatter=only_verbose(args)),
        Variable("config",          config, label="Configuration", formatter=only_verbose(args, Variable.callout_formatter)),    
    ]


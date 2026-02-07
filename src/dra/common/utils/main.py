# Common utilities for the application "main" files.

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from dra.common.deep_search import DeepSearch
from dra.common.markdown import MarkdownObserver
from dra.common.observer import Observer, Observers
from dra.common.utils.paths import resolve_path, resolve_and_require_path
from dra.common.variables import Variable

from dra.ux.display import Display
from dra.ux.rich import RichDisplay

class ParserUtil():
    def __init__(self, which_app: str, app_name: str, ux_title: str, description: str):
        self.which_app = which_app
        self.app_name = app_name
        self.ux_title = ux_title
        self.description = description

        self.parser = self.make_parser()
        self.args: argparse.Namespace = None      # set by self.process_args()
        self.processed_args: dict[str,any] = {}   # set by  self.process_args()

        self.defaults = {
            'output-dir': "./output",
            'templates-dir': "./templates",
            'markdown-report': f'{self.which_app}_research_report.md',
            'markdown-yaml-header': None,
            'provider': 'openai',
            'research-model': 'gpt-4o',
            'mcp-agent-config': self.make_def_mcp_agent_config_path(),
            'temperature': 0.7,
            'max-iterations': 25,
            'max-tokens': 500000,
            'max-cost-dollars': 2.0,
            'max-time-minutes': 15,
        }

    def make_parser(self) -> argparse.ArgumentParser:
        self.parser = argparse.ArgumentParser(
            description=self.description,
            epilog="""
    Due to current limitations, you must use either OpenAI, Anthropic, or local models
    served by ollama, and you have to tell us which one using the `--provider` argument.
    It defaults to 'openai'. The value will be used to select the correct "mcp_agent_config.yaml"
    file for configuring settings.
    """
        )
        return self.parser

    def get_default(self, key: str, default: any = None) -> any:
        if default:
            return default
        else:
            # convenience: remove leading '--' if present and change '_' to '-'.
            k = key.replace('--', '').replace('_', '-')
            return self.defaults.get(k)

    def make_def_mcp_agent_config_path(self, provider: str = "PROVIDER") -> str:
        return f"dra/apps/{self.which_app}/config/mcp_agent.config.{provider}.yaml"

    def relative_to(self, rw: str, where: str) -> str:
        return f"If the path doesn't contain a directory prefix, then the file will be {rw} in the directory given by '--{where}'."

    def read_relative_from(self, where: str) -> str:
        return self.relative_to('read', where)

    def written_relative_to(self, where: str) -> str:
        return self.relative_to('written', where)


    # Methods for adding arguments to the parser:

    def add_arg_output_dir(self, default: str = None):
        default = self.get_default("--output-dir", default)
        self.parser.add_argument(
            "--output-dir", default=default,
            help=f"Path where Excel and other output files will be saved. (Default: {default})"
        )

    def add_arg_markdown_report_path(self, default: str = None):
        default = self.get_default("--markdown-report", default)
        self.parser.add_argument(
            "--markdown-report", default=default,
            help=f"Path where a Markdown report is written. If empty, no report is generated. (Default: {default}) {self.written_relative_to('output-dir')}"
        )

    def add_arg_templates_dir(self, default: str = None):
        default = self.get_default("--templates-dir", default)
        self.parser.add_argument(
            "--templates-dir", default=default,
            help=f"Path to the directory where template files are located (e.g., for inference prompts). (Default: {default})"
        )

    def add_arg_markdown_yaml_header_template_path(self, default: str = None):
        default = self.get_default("--markdown-yaml-header", default)
        self.parser.add_argument(
            "--markdown-yaml-header", default=default,
            help=f"Path to an optional template for a YAML header to write at the beginning of the Markdown report. Useful for publishing the report on a GitHub Pages website. Ignored if --markdown-report is empty. (Default: {default}) {self.read_relative_from('template-dir')}"
        )

    def add_arg_research_model(self, default: str = None):
        default = self.get_default("--research-model", default)
        self.parser.add_argument(
            "--research-model", default=default,
            help=f"The model used the research orchestrator agent. (Default: {default}). It should be very capable."
        )

    def add_arg_provider(self, default: str = None):
        default = self.get_default("--provider", default)
        self.parser.add_argument(
            "--provider", default=default,
            choices=["openai", "anthropic", "ollama"], 
            help=f"The inference provider. Where is the model served? See the note at the bottom of this help. (Default: {default})"
        )

    def add_arg_temperature(self, default: float = None):
        default = self.get_default("--temperature", default)
        self.parser.add_argument(
            "--temperature", default=default,
            type=float,
            help=f"The 'temperature' used during inference calls to models, between 0.0 and 1.0. (Default: {default})"
        )

    def add_arg_max_iterations(self, default: int = None):
        default = self.get_default("--max-iterations", default)
        self.parser.add_argument(
            "--max-iterations", default=default,
            type=int,
            help=f"The maximum number of iterations for inference/analysis passes. (Default: {default}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 1)"
        )

    def add_arg_max_tokens(self, default: int = None):
        default = self.get_default("--max-tokens", default)
        self.parser.add_argument(
            "--max-tokens", default=default,
            type=int,
            help=f"The maximum number of tokens for inference passes. (Default: {default}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 10000)"
        )

    def add_arg_max_cost_dollars(self, default: float = None):
        default = self.get_default("--max-cost-dollars", default)
        self.parser.add_argument(
            "--max-cost-dollars", default=default,
            type=float,
            help=f"The maximum total cost in USD allowed for inference calls. (Default: {default}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 1.00)"
        )

    def add_arg_max_time_minutes(self, default: int = None):
        default = self.get_default("--max-time-minutes", default)
        self.parser.add_argument(
            "--max-time-minutes", default=default,
            type=int,
            help=f"The maximum number of time in minutes allowed for inference passes. (Default: {default}, but a lower value will be used if --short-run is used. Values <= 0 will be converted to 10)"
        )

    def add_arg_mcp_agent_config_path(self, default: str = None):
        default = self.get_default("--mcp-agent-config", default)
        self.parser.add_argument(
            "--mcp-agent-config", default=default,
            help=f"Path to the mcp_agent_config.yaml file for configuration settings. (Default: {default}) Specify an absolute path or a path relative to the project's \"src\" directory. Or, pass '' or None to have the mcp_agent library search for mcp_agent.config.yaml in the root directory, ./.mcp-agent, or ~/.mcp-agent/, as described in mcp-agent's documentation."
        )

    def add_arg_short_run(self):
        self.parser.add_argument(
            '--short-run',
            action='store_true',
            help="Sets some low maximum thresholds to create a shorter run. This is primarily a debugging tool, as lower iterations, for example, means lower quality results."
        )

    def add_arg_verbose(self):
        self.parser.add_argument(
            '--verbose',
            action='store_true',
            help="Print some extra output. Useful for some testing and debugging scenarios."
        )

        
    def process_args(self):
        self.args = self.parser.parse_args()

        # Ensure output directory exists
        output_dir_path = Path(self.args.output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        markdown_report_path = None
        if self.args.markdown_report:
            markdown_report_path = resolve_path(self.args.markdown_report, output_dir_path)

        templates_dir_path = Path(self.args.templates_dir)
        if not templates_dir_path.exists():
            raise ValueError(f"Prompt directory '{templates_dir_path}' doesn't exist!")

        markdown_yaml_header_path = None
        if self.args.markdown_yaml_header:
            markdown_yaml_header_path = resolve_and_require_path(self.args.markdown_yaml_header, templates_dir_path)

        # If the default value for the mcp_agent_config_path is used, then replace it
        # with the same string but with PROVIDER replaced by the actual provider value.
        mcp_agent_config_path = None
        file = self.args.mcp_agent_config
        if file:
            if file.find("PROVIDER") >= 0:
                provider = self.args.provider
                file = file.replace("PROVIDER", provider)
            # There is no alternative parent path searched for this argument, so we pass None.
            mcp_agent_config_path = resolve_and_require_path(file, None)

        temperature = self.args.temperature
        if self.args.temperature < 0.0:
            temperature = 0.0
        if self.args.temperature > 1.0:
            temperature = 1.0
        
        max_iterations = 1 if self.args.short_run else self.args.max_iterations
        if max_iterations < 1:
            max_iterations = 1

        max_tokens = 10000 if self.args.short_run else self.args.max_tokens
        if max_tokens < 1:
            max_tokens = 10000

        max_cost_dollars = 1.00 if self.args.short_run else self.args.max_cost_dollars
        if max_cost_dollars <= 0.0:
            max_cost_dollars = 1.00

        max_time_minutes = 10 if self.args.short_run else self.args.max_time_minutes
        if max_time_minutes < 1:
            max_time_minutes = 10

        # Initialize the display and observers.
        display = RichDisplay(self.ux_title)
        observers_d = {'display': display}

        if markdown_yaml_header_path:
            mo = MarkdownObserver(self.ux_title, markdown_yaml_header_path)
            observers_d['markdown'] = mo
        
        observers = Observers(observers=observers_d)

        self.processed_args = {
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M%:%S'),
            'display': display,
            'observers': observers,
            "output_dir_path": output_dir_path,
            "templates_dir_path": templates_dir_path,
            "markdown_report_path": markdown_report_path,
            "yaml_header_template_path": markdown_yaml_header_path,
            "mcp_agent_config_path": mcp_agent_config_path,
            "temperature": temperature, 
            "max_iterations": max_iterations,
            "max_tokens": max_tokens,
            "max_cost_dollars": max_cost_dollars,
            "max_time_minutes": max_time_minutes,
            "ux_title": self.ux_title,
        }

    def only_verbose(self, formatter: str = 'str') -> str | None:
        return formatter if self.args.verbose else None

    def common_variables(self) -> list[Variable]:    
        return [
            Variable("provider",                   self.args.provider, kind='provider'),
            Variable("research_model",             self.args.research_model, kind='code'),
            Variable("templates_dir_path",         self.processed_args['templates_dir_path'], kind='file'),
            Variable("output_dir_path",            self.processed_args['output_dir_path'], kind='file'),
            Variable("research_report_path",       self.processed_args['markdown_report_path'], kind='file'),
            Variable("yaml_header_template_path",  self.processed_args['yaml_header_template_path'], kind='file'),
            Variable("mcp_agent_config_path",      self.processed_args['mcp_agent_config_path'], kind='file'),
        ]

    def only_verbose_common_vars(self) -> list[Variable]:
        fmt = self.only_verbose()
        return [
            Variable("verbose",           self.args.verbose, kind=fmt),
            Variable("short_run",         self.args.short_run, kind=fmt),
            Variable("observers",         self.processed_args['observers'], kind=fmt),
            Variable("temperature",       self.processed_args['temperature'], label="LLM Temperature", kind=fmt), 
            Variable("max_iterations",    self.processed_args['max_iterations'], label="LLM Max Iterations", kind=fmt),
            Variable("max_tokens",        self.processed_args['max_tokens'], label="LLM Max Inference Tokens", kind=fmt),
            Variable("max_cost_dollars",  self.processed_args['max_cost_dollars'], label="LLM Max Inference cost in USD", kind=fmt),
            Variable("max_time_minutes",  self.processed_args['max_time_minutes'], label="LLM Max Inference time in minutes", kind=fmt),
            Variable("update_iteration_frequency_secs", # TODO: make user configurable??
                                          1.0, label="Frequency in Seconds for Updating the Display", kind=fmt),
            Variable("ux_title",          self.processed_args['ux_title'], label = "UX Title", kind=fmt),
        ]


#!/usr/bin/env python
"""
Deep Orchestrator Medical Research Example

This example demonstrates the Deep Orchestrator (AdaptiveOrchestrator) for medical research with:
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

from dra.common.deep_search import DeepSearch
from dra.common.tasks import BaseTask, GenerateTask, AgentTask
from dra.common.utils.main import ParserUtil
from dra.common.utils.paths import resolve_path, resolve_and_require_path
from dra.common.variables import Variable
from dra.ux.display import Display


if __name__ == "__main__":

    def_medical_research_agent_prompt_file = "medical_research_agent.md"
    
    which_app='medical'
    app_name = "medical_deep_research"
    ux_title='Medical Deep Research Agent'
    description = "Medical Deep Research using orchestrated AI agents"
    parser_util = ParserUtil(which_app, app_name, ux_title, description)

    parser_util.parser.add_argument(
        "-q", "--query",
        required=True,
        help=f"A quoted string with your research query."
    )
    parser_util.add_arg_output_dir()
    parser_util.add_arg_markdown_report_path()
    parser_util.add_arg_templates_dir()
    parser_util.parser.add_argument(
        "--medical-research-prompt-path",
        default=def_medical_research_agent_prompt_file,
        help=f"Path where the main research agent prompt file is located. (Default: {def_medical_research_agent_prompt_file}) {parser_util.read_relative_from('templates-dir')}"
    )
    parser_util.add_arg_markdown_yaml_header_template_path()
    parser_util.add_arg_research_model()
    parser_util.add_arg_provider()
    parser_util.add_arg_mcp_agent_config_path()
    parser_util.add_arg_temperature()
    parser_util.add_arg_max_iterations()
    parser_util.add_arg_max_tokens()
    parser_util.add_arg_max_cost_dollars()
    parser_util.add_arg_max_time_minutes()
    parser_util.add_arg_short_run()
    parser_util.add_arg_verbose()
    
    parser_util.process_args()
    
    output_dir_path = parser_util.processed_args['output_dir_path']    
    templates_dir_path = parser_util.processed_args['templates_dir_path']
    # This must exist:
    medical_research_prompt_path = resolve_and_require_path(
        parser_util.args.medical_research_prompt_path, templates_dir_path)

    # The variables dict contains values used by the app components, labels 
    # for display purposes and a format for knowing how to render the value.
    # Start with values we want to see at the top:
    variables_list = [
        Variable("start_time",  processed_args['start_time']),
        Variable("query",       args.query),
    ]
    # Add common values across apps:
    variables_list.extend(parser_util.common_variables())
    
    # Finish with the remaining custom variables for this app and "verbose" variables:
    variables_list.extend([
        Variable("medical_research_prompt_path", medical_research_prompt_path, kind='file'),
    ])
    variables_list.extend(parser_util.only_verbose_common_vars())

    variables = dict([(v.key, v) for v in variables_list])

    tasks = [
        GenerateTask(
            name="medical_research",
            title="📊 Medical Research Result",
            model_name=args.research_model,
            prompt_template_path=medical_research_prompt_path,
            output_dir_path=output_dir_path,
            properties=variables),
    ]

    # Create configuration for the Deep Orchestrator
    # To add additional servers, define them in mcp_agent.config.yaml,
    # then add them by name the list passed for `available_servers`.
    # See the project README for details.

    config: DeepOrchestratorConfig = DeepSearch.make_default_config(
        parser_util.args.short_run,
        "MedicalDeepResearcher",
        ["fetch", "filesystem", "medical-datasets"])
    

    variables["config"] = Variable("config", config, 
        label="Configuration", 
        kind=parser_util.only_verbose())

    observers = parser_util.processed_args['observers']    
    display = parser_util.processed_args['display']

    deep_search = DeepSearch(
        app_name=app_name,
        provider=parser_util.args.provider,
        config=config,
        tasks=tasks,
        output_dir_path=output_dir_path,
        display=display,
        observers=observers,
        variables=variables)

    asyncio.run(deep_search.run())

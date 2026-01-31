# Unit tests for the "deep search" module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, shutil, sys

from tests.utils import (
    nonempty_text,
    no_brace_text,
    no_brace_non_empty_text,
)

from finance_deep_search.deep_search import DeepSearch
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

output_path = './tests/output/META'

class TestDeepSearch(unittest.TestCase):
    """
    Test DeepSearch. TODO
    """

    @classmethod
    def setUpClass(cls):
        os.makedirs(output_path, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(output_path)

    def make(self,
            app_name: str = 'DeepSearchTest',
            config: DeepOrchestratorConfig = None,
            ticker: str = 'META',
            company_name: str = 'Meta Platforms, Inc.',
            reporting_currency: str = 'USD',
            orchestrator_model_name: str = 'llama3.2:3B',
            excel_writer_model_name: str = 'llama3.2:3B',
            provider: str = 'ollama',
            prompts_dir: str = 'finance_deep_search/prompts',
            financial_research_prompt_path: str = 'financial_research_agent.md',
            excel_writer_agent_prompt_path: str = 'excel_writer_agent.md',
            output_spreadsheet_path: str = f'{output_path}/financials_META.xlsx',
            short_run: bool = False,
            verbose: bool = False):
        return DeepSearch(
            app_name = app_name,
            config = config,
            ticker = ticker,
            company_name = company_name,
            reporting_currency = reporting_currency,
            orchestrator_model_name = orchestrator_model_name,
            excel_writer_model_name = excel_writer_model_name,
            provider = provider,
            prompts_dir = prompts_dir,
            financial_research_prompt_path = financial_research_prompt_path,
            excel_writer_agent_prompt_path = excel_writer_agent_prompt_path,
            output_path = output_path,
            output_spreadsheet_path = output_spreadsheet_path,
            short_run = short_run,
            verbose = verbose,
        )

if __name__ == "__main__":
    unittest.main()
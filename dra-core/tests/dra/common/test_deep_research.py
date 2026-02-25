# Unit tests for the "deep research" module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import unittest
from pathlib import Path
import os, re, shutil, sys

from dra.core.common.deep_research import DeepResearch
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

output_dir = './tests/output/META'
output_dir_path = Path(output_dir)

class TestDeepResearch(unittest.TestCase):
    """
    Test DeepResearch. TODO
    """

    @classmethod
    def setUpClass(cls):
        os.makedirs(output_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(output_dir)

    # TODO: This will fail if executed as the constructor args have changed!
    def make(self,
            app_name: str = 'DeepResearchTest',
            config: DeepOrchestratorConfig = None,
            ticker: str = 'META',
            company_name: str = 'Meta Platforms, Inc.',
            reporting_currency: str = 'USD',
            research_model_name: str = 'llama3.2:3B',
            excel_writer_model_name: str = 'llama3.2:3B',
            provider: str = 'ollama',
            templates_dir: str = 'dra/apps/finance/templates',
            financial_research_prompt_path: str = 'financial_research_agent.md',
            excel_writer_agent_prompt_path: str = 'excel_writer_agent.md',
            output_spreadsheet_path: str = output_dir_path / "META_financials.xlsx",
            short_run: bool = False,
            verbose: bool = False):
        return DeepResearch(
            app_name = app_name,
            config = config,
            ticker = ticker,
            company_name = company_name,
            reporting_currency = reporting_currency,
            research_model_name = research_model_name,
            excel_writer_model_name = excel_writer_model_name,
            provider = provider,
            templates_dir = templates_dir,
            financial_research_prompt_path = financial_research_prompt_path,
            excel_writer_agent_prompt_path = excel_writer_agent_prompt_path,
            output_dir_path = output_dir_path,
            output_spreadsheet_path = output_spreadsheet_path,
            short_run = short_run,
            verbose = verbose,
        )

if __name__ == "__main__":
    unittest.main()
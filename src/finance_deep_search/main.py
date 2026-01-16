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

if __name__ == "__main__":

    def_app_name = "finance_deep_research"

    parser = argparse.ArgumentParser(
        description="Deep Finance Research using orchestrated AI agents"
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
        "--prompts-path",
        default="./prompts",
        help="Path where prompt files are located. (Default: ./prompts)"
    )
    parser.add_argument(
        "--output-path",
        default="./output",
        help="Path where Excel output files will be saved. (Default: ./output)"
    )
    parser.add_argument(
        "--om", "--orchestrator-model",
        default="gpt-4o",
        help="The model used the orchestrator agent (default: gpt-4o); it should be very capable"
    )
    parser.add_argument(
        "--rm", "--report-generation-model",
        default="o4-mini",
        help="The model used for report generation (default: o4-mini); a less powerful model is sufficient"
    )
    parser.add_argument(
        "-u", "--ux",
        choices=["rich", "markdown"],
        default="rich",
        help="The 'UX' to use. Use 'rich' (the default) for a rich console UX and 'markdown' for streaming updates in markdown syntax."
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print some extra output. Useful for some testing and debugging scenarios."
    )
    parser.add_argument(
        "-n", "--noop",
        action='store_true',
        help="Just print some things you'll do, but don't actually do them."
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Change to example directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    company = args.company_name
    if not company:
        company = f"(inferred from the ticker symbol: {args.ticker})"

    if args.verbose:
        pwd = os.path.dirname(os.path.realpath(__file__))
        print(f"""
{def_app_name}:
  Ticker:              {args.ticker}
  Company:             {args.company_name}
  Models:
    Orchestrator:      {args.om}
    Report generation: {args.rm}
  UX:                  {args.ux}
  Prompts path:        {args.prompts_path}
  Output path:         {args.output_path}
  Main path:           {sys.argv[0]}
  Current working dir: {pwd}
  Verbose?             {args.verbose}
  No op?               {args.noop}
""")
        time.sleep(2.0)  # Just to give the user time to see the above before the UX starts.

    # Run the example
    if args.ux == "rich":
        from ux.rich import rich_main
        asyncio.run(rich_main(def_app_name,
            args.ticker, args.company_name, args.om, args.rm, 
            args.prompts_path, args.output_path, args.verbose, args.noop))
    elif args.ux == "markdown":
        from ux.markdown import markdown_main
        asyncio.run(markdown_main(def_app_name,
            args.ticker, args.company_name, args.om, args.rm, 
            args.prompts_path, args.output_path, args.verbose, args.noop))

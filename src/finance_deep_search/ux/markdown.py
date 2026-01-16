#!/usr/bin/env python
"""
The Markdown-formatted streaming output version of Deep Orchestrator Finance Research Example
"""

import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

async def markdown_main(
    app_name: str,
    ticker: str,
    company_name: str,
    orchestrator_model: str,
    report_generation_model: str,
    prompts_path: str,
    output_path: str,
    verbose: bool,
    noop: bool):

    msg = "Inside markdown_main: Markdown UX support is TODO."
    if noop:
        print(f"WARNING: {msg}")
    else:
        raise Error(msg)

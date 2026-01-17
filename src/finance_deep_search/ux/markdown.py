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
from typing import Callable

from deep_search import DeepSearch

class MarkdownDeepOrchestratorMonitor():
    """Markdown-based monitor to expose all internal state of the Deep Orchestrator"""

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()


async def markdown_main(
    args: argparse.Namespace, 
    config: DeepOrchestratorConfig,
    deep_search: DeepSearch,
    make_monitor: Callable[[DeepOrchestrator], MarkdownDeepOrchestratorMonitor]):

    if args.noop:
        print(f"Inside markdown_main. Returning...")
        return
    else:
        raise Error("Markdown support TODO.")
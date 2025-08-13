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

import asyncio
import os
import sys
import time
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import (
    DeepOrchestratorConfig,
    ExecutionConfig,
    BudgetConfig,
    PolicyConfig,
    ContextConfig,
    CacheConfig,
)
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams

app = MCPApp(name="finance_deep_research")

console = Console(highlight=False, soft_wrap=False, emoji=False)


class DeepOrchestratorMonitor:
    """Monitor to expose all internal state of the Deep Orchestrator"""

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()

    def get_budget_table(self) -> Table:
        """Get budget status as a table"""
        budget = self.orchestrator.budget
        usage = budget.get_usage_pct()
        budget.get_remaining()

        table = Table(title="💰 Budget", box=box.ROUNDED, show_header=True)
        table.add_column("Resource", style="cyan")
        table.add_column("Used", style="yellow")
        table.add_column("Limit", style="green")
        table.add_column("Usage %", style="magenta")

        # Tokens
        table.add_row(
            "Tokens",
            f"{budget.tokens_used:,}",
            f"{budget.max_tokens:,}",
            f"{usage['tokens']:.1%}",
        )

        # Cost
        table.add_row(
            "Cost",
            f"${budget.cost_incurred:.3f}",
            f"${budget.max_cost:.2f}",
            f"{usage['cost']:.1%}",
        )

        # Time
        elapsed = datetime.now(budget.start_time.tzinfo) - budget.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        table.add_row(
            "Time",
            f"{elapsed_minutes:.1f} min",
            f"{budget.max_time_minutes} min",
            f"{usage['time']:.1%}",
        )

        return table

    def get_queue_tree(self) -> Tree:
        """Get task queue as a tree"""
        queue = self.orchestrator.queue
        tree = Tree("📋 Task Queue")

        # Completed steps
        if queue.completed_steps:
            completed = tree.add("[green]✅ Completed Steps")
            for step in queue.completed_steps[-2:]:  # Last 2 steps only
                step_node = completed.add(f"[dim]{step.description[:60]}...")
                # Show first 3 tasks if many, otherwise all
                tasks_to_show = step.tasks[:3] if len(step.tasks) > 3 else step.tasks
                for task in tasks_to_show:
                    if task.status == "completed":
                        icon = "[green]✓[/green]"
                    elif task.status == "failed":
                        icon = "[red]✗[/red]"
                    else:
                        icon = "•"
                    step_node.add(f"[dim]{icon} {task.description[:40]}...")
                if len(step.tasks) > 3:
                    step_node.add(f"[dim italic]... +{len(step.tasks) - 3} more tasks")

        # Current/Active step - prioritize showing active and failed tasks
        current_step = queue.get_next_step()
        if current_step:
            active = tree.add("[yellow]▶ Active Step")
            active_node = active.add(f"[yellow]{current_step.description[:60]}...")

            # Sort tasks to prioritize: in_progress > failed > pending > completed
            def task_priority(task):
                priorities = {
                    "in_progress": 0,
                    "failed": 1,
                    "pending": 2,
                    "completed": 3,
                }
                return priorities.get(task.status, 4)

            sorted_tasks = sorted(current_step.tasks, key=task_priority)
            tasks_to_show = sorted_tasks[:5]  # Show up to 5 for active step

            for task in tasks_to_show:
                if task.status == "in_progress":
                    icon = "[yellow]⟳[/yellow]"
                elif task.status == "failed":
                    icon = "[red]✗[/red]"
                elif task.status == "completed":
                    icon = "[green]✓[/green]"
                else:
                    icon = "•"
                active_node.add(f"{icon} {task.description[:40]}...")

            # Show remaining count with status breakdown if needed
            remaining = len(current_step.tasks) - len(tasks_to_show)
            if remaining > 0:
                # Count by status for the remaining tasks
                status_counts = {}
                for task in sorted_tasks[4:]:
                    status_counts[task.status] = status_counts.get(task.status, 0) + 1

                if status_counts:
                    parts = []
                    if status_counts.get("pending", 0) > 0:
                        parts.append(f"{status_counts['pending']} pending")
                    if status_counts.get("completed", 0) > 0:
                        parts.append(f"{status_counts['completed']} done")
                    active_node.add(
                        f"[dim italic]... +{remaining} more ({', '.join(parts)})"
                    )

        # Pending steps (just count)
        if queue.pending_steps:
            _pending = tree.add(f"[dim]⏳ {len(queue.pending_steps)} Pending Steps")

        # Failed tasks summary if any
        if queue.failed_task_names:
            failed = tree.add(f"[red]❌ {len(queue.failed_task_names)} Failed Tasks")
            for task_name in list(queue.failed_task_names)[:2]:
                failed.add(f"[red dim]{task_name}")

        # Queue summary
        tree.add(f"[blue]📊 {queue.get_progress_summary()}")

        return tree

    def get_plan_table(self) -> Table:
        """Get the current plan as a table"""
        table = Table(title="📝 Current Plan", box=box.ROUNDED, show_header=True)
        table.add_column("Step", style="cyan", width=3)
        table.add_column("Description", style="yellow")
        table.add_column("Tasks", style="green", width=3)
        table.add_column("Status", style="magenta", width=10)

        if (
            not hasattr(self.orchestrator, "current_plan")
            or not self.orchestrator.current_plan
        ):
            table.add_row("-", "No plan created yet", "-", "-")
            return table

        plan = self.orchestrator.current_plan
        queue = self.orchestrator.queue

        for i, step in enumerate(plan.steps, 1):
            # Determine status
            if step in queue.completed_steps:
                status = "[green]✓ Done[/green]"
            elif step == queue.get_next_step():
                status = "[yellow]→ Active[/yellow]"
            else:
                status = "[dim]Pending[/dim]"

            table.add_row(
                str(i),
                step.description[:60] + "..."
                if len(step.description) > 60
                else step.description,
                str(len(step.tasks)),
                status,
            )

        return table

    def get_token_stats_panel(self) -> Panel:
        """Get token usage statistics"""
        lines = []

        # Get token breakdown from context if available
        if self.orchestrator.context and hasattr(
            self.orchestrator.context, "token_counter"
        ):
            counter = self.orchestrator.context.token_counter
            if counter:
                # Get summary
                summary = counter.get_summary()
                if summary and hasattr(summary, "usage"):
                    usage = summary.usage
                    lines.append(f"[cyan]Total Tokens:[/cyan] {usage.total_tokens:,}")
                    lines.append(f"[cyan]Input Tokens:[/cyan] {usage.input_tokens:,}")
                    lines.append(f"[cyan]Output Tokens:[/cyan] {usage.output_tokens:,}")

                    # Cost if available
                    if hasattr(summary, "cost"):
                        lines.append(
                            f"[cyan]Estimated Cost:[/cyan] ${summary.cost:.4f}"
                        )

                    # Get top consumers
                    node = counter.find_node(self.orchestrator.name)
                    if node and node.children:
                        lines.append("\n[yellow]Top Consumers:[/yellow]")
                        sorted_children = sorted(
                            node.children,
                            key=lambda n: n.usage.total_tokens,
                            reverse=True,
                        )
                        for child in sorted_children[:3]:
                            pct = (
                                (child.usage.total_tokens / usage.total_tokens * 100)
                                if usage.total_tokens > 0
                                else 0
                            )
                            lines.append(
                                f"  • {child.name[:30]}: {child.usage.total_tokens:,} ({pct:.1f}%)"
                            )

        if not lines:
            lines.append("[dim]No token usage data available yet[/dim]")

        return Panel("\n".join(lines), title="📊 Token Usage", border_style="blue")

    def get_memory_panel(self) -> Panel:
        """Get memory status as a panel"""
        memory = self.orchestrator.memory
        stats = memory.get_stats()

        lines = [
            f"[cyan]Artifacts:[/cyan] {stats['artifacts']}",
            f"[cyan]Knowledge Items:[/cyan] {stats['knowledge_items']}",
            f"[cyan]Task Results:[/cyan] {stats['task_results']}",
            f"[cyan]Categories:[/cyan] {stats['knowledge_categories']}",
            f"[cyan]Est. Tokens:[/cyan] {stats['estimated_tokens']:,}",
        ]

        # Add recent knowledge items
        if memory.knowledge:
            lines.append("\n[yellow]Recent Knowledge:[/yellow]")
            for item in memory.knowledge[-3:]:
                lines.append(f"  • {item.key[:40]}: {str(item.value)[:40]}...")

        content = "\n".join(lines)
        return Panel(content, title="🧠 Memory", border_style="blue")

    def get_agents_table(self) -> Table:
        """Get agent cache status"""
        cache = self.orchestrator.agent_cache

        table = Table(title="🤖 Agent Cache", box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Cached Agents", str(len(cache.cache)))
        table.add_row("Cache Hits", str(cache.hits))
        table.add_row("Cache Misses", str(cache.misses))

        if cache.hits + cache.misses > 0:
            hit_rate = cache.hits / (cache.hits + cache.misses)
            table.add_row("Hit Rate", f"{hit_rate:.1%}")

        # Show cached agent names
        if cache.cache:
            agent_names = []
            for key, agent in list(cache.cache.items())[:3]:
                agent_names.append(agent.name)
            if agent_names:
                table.add_row("Recent", ", ".join(agent_names))

        return table

    def get_policy_panel(self) -> Panel:
        """Get policy engine status"""
        policy = self.orchestrator.policy

        lines = [
            f"[cyan]Consecutive Failures:[/cyan] {policy.consecutive_failures}/{policy.max_consecutive_failures}",
            f"[cyan]Total Successes:[/cyan] {policy.total_successes}",
            f"[cyan]Total Failures:[/cyan] {policy.total_failures}",
            f"[cyan]Failure Rate:[/cyan] {policy.get_failure_rate():.1%}",
        ]

        return Panel("\n".join(lines), title="⚙️ Policy Engine", border_style="yellow")

    def get_status_summary(self) -> Panel:
        """Get overall status summary"""
        elapsed = time.time() - self.start_time

        lines = [
            f"[cyan]Objective:[/cyan]\n        {self.orchestrator.objective[:100]}...",
            f"[cyan]Iteration:[/cyan] {self.orchestrator.iteration}/{self.orchestrator.config.execution.max_iterations}",
            f"[cyan]Replans:[/cyan] {self.orchestrator.replan_count}/{self.orchestrator.config.execution.max_replans}",
            f"[cyan]Elapsed:[/cyan] {elapsed:.1f}s",
        ]

        return Panel("\n".join(lines), title="📊 Status", border_style="green")


def create_display_layout() -> Layout:
    """Create the display layout"""
    layout = Layout()

    # Main structure
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top_section", size=12),
        Layout(name="buffer", size=6),
        Layout(name="bottom_section", size=10),
    )

    # Top section - queue, plan, and memory
    layout["top_section"].split_row(
        Layout(name="queue", ratio=3),  # More space for queue/plan
        Layout(name="memory", ratio=2),  # Less for memory
    )

    # Bottom section - budget, status, and agents
    layout["bottom_section"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=1),
    )

    return layout


def update_display(layout: Layout, monitor: DeepOrchestratorMonitor):
    """Update the display with current state"""

    # Header
    layout["header"].update(
        Panel("Deep Finance Research", style="bold blue")
    )

    layout["buffer"].update("")

    # Top section - Queue and Plan side by side
    queue_plan_content = Columns(
        [monitor.get_queue_tree(), monitor.get_plan_table()],
        padding=(1, 2),  # Add padding between columns
    )
    layout["queue"].update(queue_plan_content)

    # Memory section
    layout["memory"].update(monitor.get_memory_panel())

    # Bottom section
    # Left column - Budget
    layout["left"].update(monitor.get_budget_table())

    # Center column - Status
    layout["center"].update(monitor.get_status_summary())

    # Right column - Combined Policy and Agents in a vertical layout
    right_content = Layout()
    right_content.split_column(
        Layout(monitor.get_policy_panel(), size=7),
        Layout(monitor.get_agents_table(), size=10),
    )
    layout["right"].update(right_content)


async def main():

    # Initialize MCP App
    app = MCPApp(name="finance_deep_research")

    async with app.run() as mcp_app:
        context = mcp_app.context
        logger = mcp_app.logger

        # Configure filesystem server with current directory
        context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        # Create configuration for the Deep Orchestrator
        config = DeepOrchestratorConfig(
            name="DeepFinancialResearcher",
            available_servers=["fetch", "filesystem"],
            execution=ExecutionConfig(
                max_iterations=25,
                max_replans=2,
                max_task_retries=5,
                enable_parallel=True,
                enable_filesystem=True,
            ),
            budget=BudgetConfig(
                max_tokens=100000,
                max_cost=1.00,
                max_time_minutes=10,
            ),
        )

        # Create the Deep Orchestrator with configuration
        orchestrator = DeepOrchestrator(
            llm_factory=OpenAIAugmentedLLM,
            config=config,
            context=context,
        )

        # Create monitor for state visibility
        monitor = DeepOrchestratorMonitor(orchestrator)

        # Create display layout
        layout = create_display_layout()

        # Define the financial research task
        task = r'''
        # Deep Research Agent — Tech Financials (General)

        Role: You are a meticulous financial analyst. Collect, verify, and structure all information needed to build a tech-style financial profile for Meta platforms (stock ticker: META). Prefer primary sources and publicly accessible secondary/consensus sources. Do not guess; return `null` + an explanation when a number cannot be substantiated.

        ## Inputs
        - company_name: Meta Platforms, Inc.
        - ticker: META
        - hq_country: US
        - reporting_currency: USD
        - units: $ millions

        ## Objectives
        1. Gather historical financials (last 3 fiscal years) and the most recent TTM where available.
        2. Capture company guidance (revenue, opex/capex ranges, margin commentary).
        3. Add Street/consensus and at least two bank projections for next FY (and next+1 if easily available) using public excerpts.
        4. Extract or compute line items aligned to a tech P&L:
        - Revenue by stream (e.g., Ads / Subscriptions / Hardware / Payments & Other)
        - Cost of Revenue detail (infrastructure, depreciation & amortization, partner/content costs, payment processing & other)
        - Opex: R&D, Sales & Marketing, G&A
        - Non-operating: interest income/expense, other income/expense
        - Tax expense and effective tax rate
        - Derived: Gross Profit, Operating Income, Net Income, margins
        5. (Optional) Cash flow & capex: Operating Cash Flow, Capex, FCF, FCF margin.
        6. Collect segments/KPIs if disclosed (e.g., DAU/MAU, ARPU by region, paid subs, ad impressions, price per ad, headcount, SBC).

        ## Source Priority (in order)
        1. Regulatory filings (10-K/10-Q/8-K; or local equivalents)
        2. Company Investor Relations (press releases, presentations, guidance tables)
        3. Earnings call transcripts (public pages)
        4. High-quality financial media (Reuters/FT/WSJ articles with public excerpts)
        5. Consensus snapshots (public pages)
        6. Bank research (public quotes/excerpts only; no proprietary PDFs)

        For every number: record source_url, publisher, title, date, and pinpoint (page/slide/line). Keep any direct quotes ≤ 30 words.

        ## Starter Links (public, non-paywalled when possible)
        Regulators (pick based on hq_country)
        - US (SEC EDGAR company search): https://www.sec.gov/edgar/searchedgar/companysearch

        Transcripts (public pages)
        - Motley Fool earnings call transcripts: https://www.fool.com/earnings/call-transcripts/
        - Seeking Alpha (some pages public): https://seekingalpha.com/symbol/{TICKER}/earnings
        - Company-hosted webcast pages (events/IR)

        Consensus & Estimates (public snapshots)
        - Yahoo Finance “Analysis”: https://finance.yahoo.com/quote/{TICKER}/analysis
        - Nasdaq earnings & estimates: https://www.nasdaq.com/market-activity/stocks/{TICKER}/earnings

        ## Query Patterns (use multiple)
        - "site:sec.gov 10-K {company_name}", "site:sec.gov 10-Q {company_name} revenue", "site:{company-domain} investor guidance"
        - "site:reuters.com {company_name} guidance revenue", "site:nasdaq.com {ticker} earnings estimates"
        - "site:seekingalpha.com {ticker} prepared remarks", "site:fool.com {company_name} call transcript"
        - For segments/KPIs: "{company_name} ARPU", "{company_name} DAU MAU", "{company_name} capex guidance"

        ## Computation Rules
        - Gross Profit = Revenue - Cost of Revenue
        - Operating Income = Gross Profit - (R&D + S&M + G&A)
        - Pre-Tax = Operating Income + (Interest Income - Interest Expense) + Other Inc/(Exp)
        - Net Income = Pre-Tax - Income Tax Expense
        - Margins = Metric ÷ Total Revenue
        - FCF = Operating Cash Flow - Capex; FCF Margin = FCF ÷ Revenue
        - If a sub-line isn't disclosed, leave `null` and state the imputation you considered (but did not use).

        ## Forecasting & Models
        1. Company guidance first (quarterly or annual). If quarterly: annualize transparently (document method and date).
        2. Consensus second (public snapshots). Capture revenue and EPS; operating income if available.
        3. Banks: gather ≥2 public excerpts (JPM, GS, MS, Citi, BofA, Barclays, etc.). Record value, date, and verbatim short quote.
        4. Return range + median for each forecasted metric (e.g., FY+1 revenue, capex, EPS).

        ## Validation (must include in output)
        - Sums: components → totals; segments → consolidated; opex lines → total opex.
        - Rates: effective tax = tax_expense ÷ pre_tax (report).
        - Margins recompute correctly from reported figures.
        - Period alignment: fiscal year definitions; currency/units consistent.
        - YoY deltas: flag > ±20% with a one-line explanation (pricing, mix, FX, one-offs).
        - Freshness: include the latest filing + latest guidance dates.

        ## Output (Machine-Readable JSON)
        Return a single JSON object with these top-level keys. Use `null` where unknown, and always include `sources` arrays with `id` references.

        {
        "company": "",
        "ticker": "",
        "currency": "USD",
        "units": "millions",
        "periods": ["FY2022","FY2023","FY2024","TTM","FY2025E","FY2026E"],
        "financials": {
            "revenue": {
            "streams": {
                "ads": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": ["s_ir_pr","s_10k"]},
                "subscriptions": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
                "hardware": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
                "payments_other": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []}
            },
            "total": {"FY2022": null, "FY2023": null, "FY2024": null, "TTM": null, "FY2025E": null, "sources": ["s_10k","s_consensus"]}
            },
            "cost_of_revenue": {
            "infrastructure_da": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": ["s_10k"]},
            "content_partner_costs": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
            "payments_processing_other": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
            "total": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null}
            },
            "opex": {
            "r_and_d": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": ["s_10k"]},
            "sales_marketing": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
            "g_and_a": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": []},
            "total": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null}
            },
            "non_operating": {
            "interest_income": {"FY2022": null, "FY2023": null, "FY2024": null, "sources": ["s_10k"]},
            "interest_expense": {"FY2022": null, "FY2023": null, "FY2024": null, "sources": []},
            "other_income_expense": {"FY2022": null, "FY2023": null, "FY2024": null, "sources": []}
            },
            "tax": {
            "income_tax_expense": {"FY2022": null, "FY2023": null, "FY2024": null, "sources": ["s_10k"]},
            "effective_tax_rate_percent": {"FY2022": null, "FY2023": null, "FY2024": null}
            },
            "derived": {
            "gross_profit": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null},
            "operating_income": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null},
            "net_income": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null},
            "margins_percent": {
                "gross": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null},
                "operating": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null},
                "net": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null}
            }
            },
            "cashflow": {
            "ocf": {"FY2022": null, "FY2023": null, "FY2024": null, "sources": ["s_10k_cf"]},
            "capex": {"FY2022": null, "FY2023": null, "FY2024": null, "FY2025E": null, "sources": ["s_ir_guidance"]},
            "fcf": {"FY2022": null, "FY2023": null, "FY2024": null}
            },
            "segments_kpis": {
            "segments": [],
            "kpis": []
            }
        },
        "street_and_banks": {
            "consensus": {
            "revenue_FY+1": {"value": null, "sources": ["s_consensus"]},
            "eps_FY+1": {"value": null, "sources": ["s_consensus"]}
            },
            "banks": [
            {"bank":"", "metric":"revenue_FY+1", "value": null, "date": "", "quote": "", "source":"s_bank1"},
            {"bank":"", "metric":"revenue_FY+1", "value": null, "date": "", "quote": "", "source":"s_bank2"}
            ],
            "ranges": {
            "revenue_FY+1_min": null,
            "revenue_FY+1_max": null,
            "revenue_FY+1_median": null
            }
        },
        "sources": {
            "s_10k": {"title":"Annual report","publisher":"Regulator/SEC","url":"","date":"","pinpoint":"","confidence":"high"},
            "s_10k_cf": {"title":"Cash flow statement","publisher":"Regulator/SEC","url":"","date":"","pinpoint":"","confidence":"high"},
            "s_ir_pr": {"title":"Earnings press release","publisher":"Company IR","url":"","date":"","pinpoint":"","confidence":"high"},
            "s_ir_guidance": {"title":"Guidance/Capex commentary","publisher":"Company IR","url":"","date":"","pinpoint":"","confidence":"medium"},
            "s_consensus": {"title":"Consensus snapshot","publisher":"(Yahoo/Nasdaq/Reuters)","url":"","date":"","confidence":"medium"},
            "s_bank1": {"title":"Public bank note excerpt","publisher":"","url":"","date":"","confidence":"medium"},
            "s_bank2": {"title":"Public bank note excerpt","publisher":"","url":"","date":"","confidence":"medium"}
        },
        "validation": {
            "sum_checks": [],
            "rate_checks": [],
            "margin_checks": [],
            "period_alignment": "",
            "yoy_flags": []
        },
        "notes": []
        }
        '''

        # Store plan reference for display
        orchestrator.current_plan = None

        with Live(layout, console=console, refresh_per_second=4, screen=True, transient=False) as _live:
            # Update display in background
            async def update_loop():
                while True:
                    try:
                        update_display(layout, monitor)
                        await asyncio.sleep(0.25)  # Reduced from 0.5s
                    except Exception as e:
                        logger.error(f"Display update error: {e}")
                        break

            # Start update loop
            update_task = asyncio.create_task(update_loop())

            try:
                # Run the orchestrator
                start_time = time.time()

                result = await orchestrator.generate_str(
                    message=task,
                    request_params=RequestParams(
                        model="gpt-4o-mini", temperature=0.7, max_iterations=10
                    ),
                )

                result_formatted = (
                    result[:2000] + "..." if len(result) > 2000 else result
                )

                excel_agent = Agent(
                    name="ExcelWriter",
                    instruction="""**SYSTEM:**  
                        You are a top-tier financial research analyst and spreadsheet automation expert.  

                        **USER:**  
                        Your task is to generate an Excel workbook containing key financial data for the publicly traded company identified by `{stock_ticker}`. Follow these requirements:

                        1. **Workbook creation**  
                        - Create a new Excel file at `./financials_{stock_ticker}.xlsx`.  
                        - Use a worksheet named **Financials**.  

                        2. **Data population**  
                        - Populate the sheet using the financial context provided (yields, quarterly earnings, revenue breakdowns, key ratios, etc.).  
                        - Lay out the data in a tabular format matching this style:  

                        | **Account**                              | **FY 2022** | **FY 2023** | **FY 2024** | **FY 2025E (Our Model)** | **FY 2025E (Guidance / Consensus)** |
                        |------------------------------------------|------------:|------------:|------------:|--------------------------:|-------------------------------------:|
                        | **Revenue**                              |             |             |             |                           |                                      |
                        | • Advertising                            |    112,000  |    129,000  |    146,000  |        162,000           |                                     |
                        | • Reality Labs                           |      2,000  |      3,000  |      4,000  |          5,000           |                                     |
                        | • Payments & Other                       |      4,000  |      3,000  |      3,000  |          3,000           |                                     |
                        | **Total Revenue**                         |    118,000  |    135,000  |    153,000  |        170,000           | Company: Q3 guidance ~\$49B/Q → implies FY ~\$204B annualized*; Analyst Q2 est: ~\$44.8B → implies FY ~\$179B** |
                        | **Cost of Revenue**                       |             |             |             |                           |                                      |
                        | • Infrastructure & Depreciation           |   (22,000)  |   (26,000)  |   (29,000)  |       (31,000)           |                                     |
                        | • Content/Partner Payments                |    (4,000)  |    (5,000)  |    (5,500)  |        (6,000)           |                                     |
                        | • Payments Processing & Other             |    (2,000)  |    (2,000)  |    (2,500)  |        (3,000)           |                                     |
                        | **Gross Profit**                          |     90,000  |    102,000  |    116,000  |        130,000           |                                     |
                        | **Gross Margin**                          |      76.3%  |      75.6%  |      75.8%  |       76.5%              |                                     |
                        | **Operating Expenses**                    |             |             |             |                           |                                      |
                        | • R&D                                    |   (30,000)  |   (32,000)  |   (34,000)  |        (36,000)          |                                     |
                        | • Sales & Marketing                       |   (17,000)  |   (19,000)  |   (21,000)  |        (23,000)          |                                     |
                        | • General & Admin.                       |   (11,000)  |   (12,000)  |   (12,500)  |        (13,000)          |                                    |
                        | **Operating Income**                      |     32,000  |     39,000  |     48,500  |         58,000           |                                     |
                        | **Operating Margin**                      |      27.1%  |      28.9%  |      31.7%  |       34.1%              |                                     |
                        | **Pre-Tax Income**                        |     32,600  |     40,100  |     49,700  |         59,300           |                                    |
                        | **Net Income**                            |     27,058  |     33,283  |     41,251  |         49,219           |                                     |
                        | **Net Margin**                            |      22.9%  |      24.7%  |      27.0%  |       29.0%              |                                     |
                        
                        3. **Formatting requirements**  
                        - Apply appropriate number formats for currency, percentages, and negatives (e.g. parentheses).  
                        - Bold main headers and indent bullet items.  
                        - Auto-adjust column widths.  
                        - Style the header row with a background color and bold text, and apply banded row shading.

                        4. **Implementation**  
                        - Write executable Python code using **openpyxl** or **pandas → ExcelWriter**.  
                        - Use context managers, handle missing sheets gracefully, and include brief comments.  

                        5. **Output**  
                        - Save the workbook and print a confirmation:  
                            ```
                            Created /Users/andrew_lastmile_ai/Documents/GitHub/ai-in-finance-example-app/output/financials_{stock_ticker}.xlsx with updated Financials sheet.
                            ```""",
                    context=context,
                    server_names=["excel"]
                )

                async with excel_agent:
                    excel_llm = await excel_agent.attach_llm(
                        OpenAIAugmentedLLM
                    )

                    excel_result = await excel_llm.generate_str(
                        message=result,
                        request_params=RequestParams(
                            model="gpt-4o-mini", temperature=0.7, max_iterations=10
                        ),
                    )

                execution_time = time.time() - start_time

                # Final update
                update_display(layout, monitor)

            finally:
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass

        # Show the research results
        console.print(
            Panel(
                result_formatted,
                title="📊 Financial Research Results (Preview)",
                border_style="green",
            )
        )
        
        # Show excel creation result
        if 'excel_result' in locals():
            console.print(
                Panel(
                    excel_result[:1000] + "..." if len(excel_result) > 1000 else excel_result,
                    title="📈 Excel Creation Result",
                    border_style="blue",
                )
            )

        # Display final statistics
        console.print("\n[bold cyan]📊 Final Statistics[/bold cyan]")

        # Create summary table
        summary_table = Table(title="Execution Summary", box=box.DOUBLE_EDGE)
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Time", f"{execution_time:.2f}s")
        summary_table.add_row("Iterations", str(orchestrator.iteration))
        summary_table.add_row("Replans", str(orchestrator.replan_count))
        summary_table.add_row(
            "Tasks Completed", str(len(orchestrator.queue.completed_task_names))
        )
        summary_table.add_row(
            "Tasks Failed", str(len(orchestrator.queue.failed_task_names))
        )
        summary_table.add_row(
            "Knowledge Items", str(len(orchestrator.memory.knowledge))
        )
        summary_table.add_row(
            "Artifacts Created", str(len(orchestrator.memory.artifacts))
        )
        summary_table.add_row("Agents Cached", str(len(orchestrator.agent_cache.cache)))
        summary_table.add_row(
            "Cache Hit Rate",
            f"{orchestrator.agent_cache.hits / max(1, orchestrator.agent_cache.hits + orchestrator.agent_cache.misses):.1%}",
        )

        console.print(summary_table)

        # Display budget summary
        budget_summary = orchestrator.budget.get_status_summary()
        console.print(f"\n[yellow]{budget_summary}[/yellow]")

        # Display knowledge learned
        if orchestrator.memory.knowledge:
            console.print("\n[bold cyan]🧠 Knowledge Extracted[/bold cyan]")

            knowledge_table = Table(box=box.SIMPLE)
            knowledge_table.add_column("Category", style="cyan")
            knowledge_table.add_column("Key", style="yellow")
            knowledge_table.add_column("Value", style="green", max_width=50)
            knowledge_table.add_column("Confidence", style="magenta")

            for item in orchestrator.memory.knowledge[:10]:  # Show first 10
                knowledge_table.add_row(
                    item.category,
                    item.key[:30] + "..." if len(item.key) > 30 else item.key,
                    str(item.value)[:50] + "..."
                    if len(str(item.value)) > 50
                    else str(item.value),
                    f"{item.confidence:.2f}",
                )

            console.print(knowledge_table)

        # Display token usage if available
        if context.token_counter:
            summary = context.token_counter.get_summary()
            console.print(
                f"\n[bold]Total Tokens:[/bold] {summary.usage.total_tokens:,}"
            )
            console.print(f"[bold]Total Cost:[/bold] ${summary.cost:.4f}")

        # Show workspace artifacts if any were created
        if orchestrator.memory.artifacts:
            console.print("\n[bold cyan]📁 Artifacts Created[/bold cyan]")
            for name in list(orchestrator.memory.artifacts.keys())[:5]:
                console.print(f"  • {name}")


if __name__ == "__main__":
    # Change to example directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Run the example
    asyncio.run(main())
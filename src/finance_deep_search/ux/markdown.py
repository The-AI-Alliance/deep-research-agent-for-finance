#!/usr/bin/env python
"""
The Markdown-formatted streaming output version of Deep Orchestrator Finance Research Example
"""

import argparse
import asyncio
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

from finance_deep_search.deep_search import DeepSearch

from finance_deep_search.ux.markdown_elements import (
    MarkdownElement,
    MarkdownSection,
    MarkdownTable
    MarkdownTree
)

class MarkdownDeepOrchestratorMonitor():
    """Markdown-based monitor to expose all internal state of the Deep Orchestrator"""

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()

    def get_budget_table(self) -> MarkdownTable:
        """Get budget status as a Markdown Table"""
        budget = self.orchestrator.budget
        usage = budget.get_usage_pct()
        budget.get_remaining()

        table = MarkdownTable(title="💰 Budget")
        table.add_columns([
            ("Resource", 'left'),
            ("Used",     'right')
            ("Limit",    'right')
            ("Usage %",  'right')
        ])

        # Tokens
        table.add_row([
            "Tokens",
            f"{budget.tokens_used:,}",
            f"{budget.max_tokens:,}",
            f"{usage['tokens']:.1%}",
        ])

        # Cost
        table.add_row([
            "Cost",
            f"${budget.cost_incurred:.3f}",
            f"${budget.max_cost:.2f}",
            f"{usage['cost']:.1%}",
        ])

        # Time
        elapsed = datetime.now(budget.start_time.tzinfo) - budget.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        table.add_row([
            "Time",
            f"{elapsed_minutes:.1f} min",
            f"{budget.max_time_minutes} min",
            f"{usage['time']:.1%}",
        ])

        return table

    def get_queue_tree(self) -> MarkdownTree:
        """Get task queue as a Markdown Tree"""
        queue = self.orchestrator.queue
        tree = MarkdownTree(label = "📋 Task Queue")

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

    def get_plan_table(self) -> MarkdownTable:
        """Get the current plan as a Markdown Table"""
        table = MarkdownTable(title="📝 Current Plan")
        table.add_columns(["Step", "Description", "Tasks", "Status"])

        if (
            not hasattr(self.orchestrator, "current_plan")
            or not self.orchestrator.current_plan
        ):
            table.add_row(["-", "No plan created yet", "-", "-"])
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

            table.add_row([
                str(i),
                step.description[:60] + "..."
                if len(step.description) > 60 
                else step.description,
                str(len(step.tasks)),
                status,
            ])

        return table

    # TODO: this isn't called!!
    def get_token_stats_panel(self, level: int = 1) -> MarkdownSection:
        """Get token usage statistics as a Markdown section"""
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

        return MarkdownSection(level = level, title="📊 Token Usage", content=lines)

    def get_memory_panel(self, level: int = 1) -> MarkdownSection:
        """Get memory status as a Markdown section"""
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

        return MarkdownSection(level=level, title="🧠 Memory", content=lines)

    def get_agents_table(self) -> MarkdownTable:
        """Get agent cache status as a Markdown Table"""
        cache = self.orchestrator.agent_cache

        table = MarkdownTable(title="🤖 Agent Cache")
        table.add_columns([("Metric", 'left'), ("Value", 'right')])

        table.add_row(["Cached Agents", str(len(cache.cache))])
        table.add_row(["Cache Hits", str(cache.hits)])
        table.add_row(["Cache Misses", str(cache.misses)])

        if cache.hits + cache.misses > 0:
            hit_rate = cache.hits / (cache.hits + cache.misses)
            table.add_row(["Hit Rate", f"{hit_rate:.1%}"])

        # Show cached agent names
        if cache.cache:
            agent_names = []
            for key, agent in list(cache.cache.items())[:3]:
                agent_names.append(agent.name)
            if agent_names:
                table.add_row(["Recent", ", ".join(agent_names)])

        return table

    def get_policy_panel(self, level: int = 1) -> MarkdownSection:
        """Get policy engine status as a Markdown section"""
        policy = self.orchestrator.policy

        lines = [
            f"[cyan]Consecutive Failures:[/cyan] {policy.consecutive_failures}/{policy.max_consecutive_failures}",
            f"[cyan]Total Successes:[/cyan] {policy.total_successes}",
            f"[cyan]Total Failures:[/cyan] {policy.total_failures}",
            f"[cyan]Failure Rate:[/cyan] {policy.get_failure_rate():.1%}",
        ]

        return MarkdownSection(level=level, title="⚙️ Policy Engine", content=lines)

    def get_status_summary(self, level: int = 1) -> MarkdownSection:
        """Get overall status summary as a Markdown section"""
        elapsed = time.time() - self.start_time

        lines = [
            f"[cyan]Objective:[/cyan]\n        {self.orchestrator.objective[:100]}...",
            f"[cyan]Iteration:[/cyan] {self.orchestrator.iteration}/{self.orchestrator.config.execution.max_iterations}",
            f"[cyan]Replans:[/cyan] {self.orchestrator.replan_count}/{self.orchestrator.config.execution.max_replans}",
            f"[cyan]Elapsed:[/cyan] {elapsed:.1f}s",
        ]

        return MarkdownSection(level=level, title="📊 Status", content=lines)

class MarkdownDisplay():
    def __init__(self, title: str, top_level: int = 1):
        """Create the display Markdown"""
        self.top_level: int = top_level
        self.layout = MarkdownSection(level=top_level, title=title)

        # Main structure
        layout.add_subsections(
            MarkdownSection(level=top_level+1, title="header"),
            MarkdownSection(level=top_level+1, title="top_section"),
            MarkdownSection(level=top_level+1, title="buffer"),
            MarkdownSection(level=top_level+1, title="bottom_section"),
        )

        # Top section - queue, plan, and memory
        layout["top_section"].add_subsections(
            MarkdownSection(level=top_level+2, title="queue", ratio=3),  # More space for queue/plan
            MarkdownSection(level=top_level+2, title="memory", ratio=2),  # Less for memory
        )

        # Bottom section - budget, status, and agents
        layout["bottom_section"].add_subsections(
            MarkdownSection(level=top_level+2, title="left"),
            MarkdownSection(level=top_level+2, title="center"),
            MarkdownSection(level=top_level+2, title="right"),
        )

    def update(self, monitor: RichDeepOrchestratorMonitor):
        """Update the display with the current state"""

        # Header - replace
        self.layout["header"] = MarkdownSection(level=top_level+1,
            title="Deep Finance Research", style="bold blue")

        layout["buffer"].clear()

        # Top section - Queue and Plan side by side
        queue_plan_content = [monitor.get_queue_tree(), monitor.get_plan_table()]
        top_section = layout["top_section"]
        top_section["queue"].set_subsections(queue_plan_content)

        # Memory section
        top_section["memory"].set_subsections([monitor.get_memory_panel()])

        # Bottom section
        bottom_section = layout["bottom_section"]
        
        # Left column - Budget
        bottom_section["left"].set_subsections([monitor.get_budget_table()])

        # Center column - Status
        bottom_section["center"].set_subsections([monitor.get_status_summary()])

        # Right column - Combined Policy and Agents in a vertical layout
        right_content = [monitor.get_policy_panel(), monitor.get_agents_table()]
        bottom_section["right"].set_subsections(right_content)

    def __str__(self) -> str:
        return str(layout)

    def display_final_statistics(console: Console, orchestrator: DeepOrchestrator):
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

    def display_budget_summary(console: Console, orchestrator: DeepOrchestrator):
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

    def display_token_usage(console: Console, orchestrator: DeepOrchestrator):
        """Display the token usage, if available."""
        if deep_search.token_counter:
            summary = await deep_search.token_counter.get_summary()
            if summary and hasattr(summary, "usage"):
                console.print(
                    f"\n[bold]Total Tokens:[/bold] {summary.usage.total_tokens:,}"
                )
                if hasattr(summary, "cost"):
                    console.print(f"[bold]Total Cost:[/bold] ${summary.cost:.4f}")

    def display_workspace_artifacts(console: Console, orchestrator: DeepOrchestrator):
        """Display workspace artifacts if any were created."""
        if orchestrator.memory.artifacts:
            console.print("\n[bold cyan]📁 Artifacts Created[/bold cyan]")
            for name in list(orchestrator.memory.artifacts.keys())[:5]:
                console.print(f"  • {name}")

    def display_final_data(console: Console, orchestrator: DeepOrchestrator):
        display_final_statistics(console, deep_search.orchestrator)
        display_budget_summary(console, deep_search.orchestrator)
        display_token_usage(console, deep_search.orchestrator)
        display_workspace_artifacts(console, deep_search.orchestrator)

async def markdown_main(
    args: argparse.Namespace, 
    config: DeepOrchestratorConfig,
    deep_search: DeepSearch):

    if args.noop:
        print(f"Inside markdown_main. Returning...")
        return


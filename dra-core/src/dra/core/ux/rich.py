"""
The Rich Console version of Deep Orchestrator Research Example
"""
# Allow types to self-reference during their definitions.
from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import time
from datetime import datetime
from typing import Callable

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich.columns import Columns
from rich import box

from dra.core.common.deep_research import DeepResearch
from dra.core.common.tasks import BaseTask, GenerateTask, AgentTask, TaskStatus
from dra.core.common.utils.strings import truncate
from dra.core.ux.display import Display

from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator

class RichDeepOrchestratorMonitor():
    """Rich-based monitor to expose all internal state of the Deep Orchestrator"""
    # TODO: Merge with RichDisplay

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()

    def get_budget_table(self) -> Table:
        """Get budget status as a Rich Table"""
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
        """Get task queue as a Rich Tree"""
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
        """Get the current plan as a Rich Table"""
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

    def get_memory_panel(self) -> Panel:
        """Get memory status as a Rich Panel"""
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
        """Get agent cache status as a Rich Table"""
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
        """Get policy engine status as a Rich Panel"""
        policy = self.orchestrator.policy

        lines = [
            f"[cyan]Consecutive Failures:[/cyan] {policy.consecutive_failures}/{policy.max_consecutive_failures}",
            f"[cyan]Total Successes:[/cyan] {policy.total_successes}",
            f"[cyan]Total Failures:[/cyan] {policy.total_failures}",
            f"[cyan]Failure Rate:[/cyan] {policy.get_failure_rate():.1%}",
        ]

        return Panel("\n".join(lines), title="⚙️ Policy Engine", border_style="yellow")

    def get_status_summary(self) -> Panel:
        """Get overall status summary as a Rich Panel"""
        elapsed = time.time() - self.start_time

        lines = [
            f"[cyan]Objective:[/cyan]\n        {self.orchestrator.objective[:100]}...",
            f"[cyan]Iteration:[/cyan] {self.orchestrator.iteration}/{self.orchestrator.config.execution.max_iterations}",
            f"[cyan]Replans:[/cyan] {self.orchestrator.replan_count}/{self.orchestrator.config.execution.max_replans}",
            f"[cyan]Elapsed:[/cyan] {elapsed:.1f}s",
        ]

        return Panel("\n".join(lines), title="📊 Status", border_style="green")


class RichDisplay(Display):
    """
    The Rich Display.
    To keep the logic as simple and bug free as possible, we only allow the DeepResearch instance
    to be set once, during lazy initialization, where it is changed from `None` to the 
    real instance.
    """
    def __init__(self, title: str):
        super().__init__(title, disallow_system_change=True)
        self.orchestrator: DeepOrchestrator = None
        self.monitor: RichDeepOrchestratorMonitor = None
        self.console: Console = None
        self.layout: Layout = None

        # The following will initialize the previous four attributes, if system != None
        super().__init__(title)

        self.start_time = time.time()
        self.execution_time = 0.0

    def _after_set_system(self):
        self.system.logger.info("RichDisplay._after_set_system() (self.system not None)")
        self.orchestrator = self.system.orchestrator
        self.monitor = RichDeepOrchestratorMonitor(self.orchestrator)
        self.console = Console(highlight=False, soft_wrap=False, emoji=False)
        self.layout  = self.__create_layout()
        super()._after_set_system()

    def __create_layout(self) -> Layout:
        """Create the display Rich Layout"""
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

    async def run_live(self, function: Callable[[], None]):
        with Live(self.layout, console=self.console, refresh_per_second=4, screen=True, transient=False) as _live:
            await function()

    def _do_update(self, 
        other: dict[str,any] = {},
        is_final: bool = False) -> any:
        """
        Update the display with the current state. 
        If `other['messages']` and/or `other['error_msg']` are not empty/None, then 
        format a `list[str]` with them, print it, and return the list.
        """
        # self.system.logger.info(f"RichDisplay._do_update(is_final={is_final})")
        
        # Header
        self.layout["header"].update(
            Panel("Deep Research", style="bold blue")
        )

        self.layout["buffer"].update("")

        # Top section - Queue and Plan side by side
        queue_plan_content = Columns(
            [self.monitor.get_queue_tree(), self.monitor.get_plan_table()],
            padding=(1, 2),  # Add padding between columns
        )
        self.layout["queue"].update(queue_plan_content)

        # Memory section
        self.layout["memory"].update(self.monitor.get_memory_panel())

        # Bottom section
        # Left column - Budget
        self.layout["left"].update(self.monitor.get_budget_table())

        # Center column - Status
        self.layout["center"].update(self.monitor.get_status_summary())

        # Right column - Combined Policy and Agents in a vertical layout
        right_content = Layout()
        right_content.split_column(
            Layout(self.monitor.get_policy_panel(), size=7),
            Layout(self.monitor.get_agents_table(), size=10),
        )
        self.layout["right"].update(right_content)

        self.__update_final_statistics()
        self.__update_budget_summary()
        self.__update_knowledge_summary()
        self.__update_workspace_artifacts()
        self.__update_report_results()

        if not is_final:
            return None

        # Don't allow problems here to stop execution!
        try:
            output_dir_path_msg = ''
            if self.system and hasattr(self.system, 'variables'):
                odp = self.system.variables.get('output_dir_path')
                if odp:
                    output_dir_path_msg = f"output files under {odp.value} and "

            msg_list1 = [
                "\n",
                f"Finished: See {output_dir_path_msg}log files under ./logs.",
                "\n",
            ]
            if other.get('messages'):
                msg_list1.extend(other.get('messages'))
            msg_list = [[f"[bold black]{line}[/bold black]" for line in msg_list1]]
            if other.get('error_msg'):
                msg_list.extend(['\n', f"[bold red]ERROR: {other.get('error_msg')}[/bold red]"])
            for line in msg_list:
                self.console.print(line)
                self.system.logger.info(line)
            return msg_list
        except Exception as ex:
            print(f"Exception {ex} was raised during last output messages. Continuing...")

    async def async_update(self,
        other: dict[str,any] = {},
        is_final: bool = False) -> any:
        return await self.__update_token_usage()

    def __update_final_statistics(self):
        # Display final statistics
        self.console.print("\n[bold cyan]📊 Final Statistics[/bold cyan]")
        self.execution_time = time.time() - self.start_time

        # Create summary table
        summary_table = Table(title="Execution Summary", box=box.DOUBLE_EDGE)
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Time", f"{self.execution_time:.2f}s")
        summary_table.add_row("Iterations", str(self.orchestrator.iteration))
        summary_table.add_row("Replans", str(self.orchestrator.replan_count))
        summary_table.add_row(
            "Tasks Completed", str(len(self.orchestrator.queue.completed_task_names))
        )
        summary_table.add_row(
            "Tasks Failed", str(len(self.orchestrator.queue.failed_task_names))
        )
        summary_table.add_row(
            "Knowledge Items", str(len(self.orchestrator.memory.knowledge))
        )
        summary_table.add_row(
            "Artifacts Created", str(len(self.orchestrator.memory.artifacts))
        )
        summary_table.add_row("Agents Cached", str(len(self.orchestrator.agent_cache.cache)))
        summary_table.add_row(
            "Cache Hit Rate",
            f"{self.orchestrator.agent_cache.hits / max(1, self.orchestrator.agent_cache.hits + self.orchestrator.agent_cache.misses):.1%}",
        )

        self.console.print(summary_table)

    def __update_budget_summary(self):
        # Display budget summary
        summary = self.orchestrator.budget.get_status_summary()
        self.console.print(f"\n[yellow]{summary}[/yellow]")

    def __update_knowledge_summary(self):
        # Display knowledge learned
        if self.orchestrator.memory.knowledge:
            self.console.print("\n[bold cyan]🧠 Knowledge Extracted[/bold cyan]")

            knowledge_table = Table(box=box.SIMPLE)
            knowledge_table.add_column("Category", style="cyan")
            knowledge_table.add_column("Key", style="yellow")
            knowledge_table.add_column("Value", style="green", max_width=50)
            knowledge_table.add_column("Confidence", style="magenta")

            for item in self.orchestrator.memory.knowledge[:10]:  # Show first 10
                knowledge_table.add_row(
                    item.category,
                    item.key[:30] + "..." if len(item.key) > 30 else item.key,
                    str(item.value)[:50] + "..."
                    if len(str(item.value)) > 50
                    else str(item.value),
                    f"{item.confidence:.2f}",
                )

            self.console.print(knowledge_table)

    async def __update_token_usage(self):
        """Display the token usage, if available."""
        # Due to an occasionally, apparent infinite loop bug when using ollama, we
        # don't invoke this code if serving that way.
        if self.orchestrator.context.token_counter and not self.system.provider == "ollama":
            summary = await self.orchestrator.context.token_counter.get_summary()
            if summary and hasattr(summary, "usage"):
                self.console.print(
                    f"\n[bold]Total Tokens:[/bold] {summary.usage.total_tokens:,}"
                )
                if hasattr(summary, "cost"):
                    self.console.print(f"[bold]Total Cost:[/bold] ${summary.cost:.4f}")

    def __update_workspace_artifacts(self):
        """Display workspace artifacts if any were created."""
        if self.orchestrator.memory.artifacts:
            self.console.print("\n[bold cyan]📁 Artifacts Created[/bold cyan]")
            for name in list(self.orchestrator.memory.artifacts.keys())[:5]:
                self.console.print(f"  • {name}")


    def __update_report_results(self):
        border_style = "green"
        strs = []
        for task in self.system.tasks:
            if not task.status == TaskStatus.FINISHED_OK:
                border_style = "red"            
            strs.append(truncate(str(task.result), 2000, '...'))
        
        self.console.print(
            Panel('\n'.join(strs), title=task.title, border_style=border_style))

    def __repr__(self) -> str:
        return str(self.layout)

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
from datetime import datetime, timedelta
from pathlib import Path

import json
from json.decoder import JSONDecodeError

from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from mcp_agent.workflows.deep_orchestrator.config import DeepOrchestratorConfig

from finance_deep_search.deep_search import DeepSearch

from finance_deep_search.ux.markdown_elements import (
    MarkdownElement,
    MarkdownSection,
    MarkdownTable,
    MarkdownTree
)

class MarkdownDeepOrchestratorMonitor():
    """Markdown-based monitor to expose all internal state of the Deep Orchestrator"""

    def __init__(self, orchestrator: DeepOrchestrator):
        self.orchestrator = orchestrator
        self.start_time = time.time()
        self.execution_time = self.start_time - self.start_time

    def get_budget_table(self) -> MarkdownTable:
        """Get budget status as a Markdown Table"""
        budget = self.orchestrator.budget
        usage = budget.get_usage_pct()
        budget.get_remaining()

        table = MarkdownTable(title="💰 Budget")
        table.add_columns([
            ("Resource", 'left'),
            ("Used",     'right'),
            ("Limit",    'right'),
            ("Usage %",  'right'),
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
            completed = tree.add("✅ Completed Steps")
            for step in queue.completed_steps[-2:]:  # Last 2 steps only
                step_node = completed.add(f"[dim]{step.description[:60]}...")
                # Show first 3 tasks if many, otherwise all
                tasks_to_show = step.tasks[:3] if len(step.tasks) > 3 else step.tasks
                for task in tasks_to_show:
                    if task.status == "completed":
                        icon = "✓"
                    elif task.status == "failed":
                        icon = "✗"
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
    def get_token_stats_section(self) -> MarkdownSection:
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

        return MarkdownSection(title="📊 Token Usage", content=lines)

    def get_memory_table(self) -> MarkdownTable:
        """Get memory status as a Markdown table"""
        memory = self.orchestrator.memory
        stats = memory.get_stats()

        table = MarkdownTable(title="🧠 Memory",
            columns = [("Quantity", 'left'), ("Value", 'right')])

        table.add_row(["Artifacts",       stats['artifacts']])
        table.add_row(["Knowledge Items", stats['knowledge_items']])
        table.add_row(["Task Results",    stats['task_results']])
        table.add_row(["Categories",      stats['knowledge_categories']])
        table.add_row(["Est. Tokens",     stats['estimated_tokens']])
        return table

    def get_knowledge_table(self) -> MarkdownTable:
        """Get recent knowledge items"""

        table = MarkdownTable(title="🧠 Recent Memory Knowledge (last three...)",
            columns = [("Quantity", 'left'), ("Value", 'right')])

        memory = self.orchestrator.memory
        if memory.knowledge:
            for item in memory.knowledge[-3:]:
                table.add_row([item.key[:40], str(item.value)[:40]])
        else:
            table.add_row(["None", ""])

        return table

    def get_agents_table(self) -> MarkdownTable:
        """Get agent cache status as a Markdown Table"""
        cache = self.orchestrator.agent_cache

        table = MarkdownTable(title="🤖 Agent Cache",
            columns = [("Metric", 'left'), ("Value", 'right')])

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

    def get_policy_table(self) -> MarkdownTable:
        """Get policy engine status as a Markdown section"""
        policy = self.orchestrator.policy

        table = MarkdownTable(title="⚙️ Policy Engine", 
            columns=[('Quantity', 'left'),('Value', 'right')])
        table.add_row(["Consecutive Failures", policy.consecutive_failures/policy.max_consecutive_failures])
        table.add_row(["Total Successes", policy.total_successes])
        table.add_row(["Total Failures", policy.total_failures])
        table.add_row(["Failure Rate", f"{policy.get_failure_rate():.1%}"])
        return table

    def get_status_summary_table(self) -> MarkdownTable:
        """Get overall status summary as a Markdown table"""
        self.update_execution_time()

        table = MarkdownTable(title="📊 Status", 
            columns=[('Quantity', 'left'),('Value', 'right')])
        table.add_row(["Objective", f"{self.orchestrator.objective[:100]}..."])
        table.add_row(["Iteration", self.orchestrator.iteration/self.orchestrator.config.execution.max_iterations])
        table.add_row(["Replans",   self.orchestrator.replan_count/self.orchestrator.config.execution.max_replans])
        table.add_row(["Elapsed",   self.execution_time])
        return table

    def update_execution_time(self) -> timedelta:
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        return self.execution_time

class MarkdownDisplay():
    def __init__(self, title: str,
        deep_search: DeepSearch,
        orchestrator: DeepOrchestrator, 
        monitor: MarkdownDeepOrchestratorMonitor):
        """Create the display Markdown"""
        self.layout = MarkdownSection(title=title)
        self.orchestrator = orchestrator
        self.monitor = monitor

        # Main structure
        self.layout.add_subsections({
            "top_section": MarkdownSection(title="App Runtime Stats"),
            "botton_section": MarkdownSection(title="Financial Results"),
        })

        # Top section - queue, plan, and memory
        self.layout["top_section"].add_subsections({
            "queue": MarkdownSection(title="Task Queue"),
            "plan": MarkdownSection(title="Current Plan"),
            "memory": MarkdownSection(title="Memory"),
        })

        # Bottom section - budget, status, and agents, and final results added later.
        self.layout["botton_section"].add_subsections({
            'budget': MarkdownSection(title="💰 Runtime Budget Statistics"),
            'status': MarkdownSection(title="📊 Status Summary"),
            'policy': MarkdownSection(title="⚙️ Policy Engine"),
        })

    def update(self) -> MarkdownSection:
        """Update the display with the current state"""
        self.monitor.update_execution_time()

        top_section = self.layout["top_section"]
        top_section["queue"].set_intro_content([self.monitor.get_queue_tree()])
        top_section["plan"].set_intro_content([self.monitor.get_plan_table()])
        top_section["memory"].set_intro_content([
            self.monitor.get_memory_table(),
            self.monitor.get_knowledge_table()])

        bottom_section = self.layout["botton_section"] 
        bottom_section["budget"].set_intro_content([self.monitor.get_budget_table()])
        bottom_section["status"].set_intro_content([self.monitor.get_status_summary_table()])
        bottom_section["policy"].set_intro_content(
            [self.monitor.get_policy_table(), self.monitor.get_agents_table()])
        
        return self.layout

    def __str__(self) -> str:
        return str(self.layout)

    def add_section(self, title: str, 
        content: list[MarkdownElement | str] = [], 
        subsections: dict[str, MarkdownElement] = {}) -> MarkdownSection:
        section = MarkdownSection(title=title, content=content, subsections=subsections)
        self.layout.add_subsections([section])
        return section

    def add_financial_results(self, results: str) -> MarkdownSection:
        content = []
        if isinstance(results, ChatCompletionMessage):
            content = results.content.split('\n')
            table = MarkdownTable(title="Chat Metadata",
                columns = [("Item", 'left'), ("Value", 'right')])
            table.add_row(['refusal', str(results.refusal)])
            table.add_row(['role', str(results.role)])
            table.add_row(['annotations', str(results.annotations)])
            table.add_row(['audio', str(results.audio)])
            table.add_row(['function_call', str(results.function_call)])
            table.add_row(['tool_calls', str(results.tool_calls)])
        else:
            content = [results]

        return self.add_section("📊 Financial Research Results (Preview)", [content])

    def add_excel_results(self, results: str) -> MarkdownSection:
        content = []
        try:
            obj = json.loads(results)
            # format as nested bullets:

        except (JSONDecodeError, TypeError) as err:
            deep_search.logger.warning(f"{err} raised while parsing Excel results: {results}")
            content = results.split('\n')
        return self.add_section("📈 Excel Creation Result", [content])
    

    def get_final_statistics(self) -> MarkdownSection:
        """Get final statistics for display"""

        # Create summary table
        summary_table = MarkdownTable(title="Execution Summary", 
            columns = ["Metric", "Value"])
        
        summary_table.add_row(["Total Time", f"{self.monitor.update_execution_time()}"])
        summary_table.add_row(["Iterations", str(self.orchestrator.iteration)])
        summary_table.add_row(["Replans", str(self.orchestrator.replan_count)])
        summary_table.add_row(
            ["Tasks Completed", str(len(self.orchestrator.queue.completed_task_names))]
        )
        summary_table.add_row(
            ["Tasks Failed", str(len(self.orchestrator.queue.failed_task_names))]
        )
        summary_table.add_row(
            ["Knowledge Items", str(len(self.orchestrator.memory.knowledge))]
        )
        summary_table.add_row(
            ["Artifacts Created", str(len(self.orchestrator.memory.artifacts))]
        )
        summary_table.add_row(
            ["Agents Cached", str(len(self.orchestrator.agent_cache.cache))]
        )
        summary_table.add_row(
            ["Cache Hit Rate",
            f"{self.orchestrator.agent_cache.hits / max(1, self.orchestrator.agent_cache.hits + self.orchestrator.agent_cache.misses):.1%}"]
        )
        return self.add_section("📊 Final Statistics", [summary_table])

    def get_budget_summary(self) -> MarkdownSection:
        budget_summary = self.orchestrator.budget.get_status_summary()
        return self.add_section("Budget Summary", [budget_summary])

    def get_knowledge_summary(self) -> MarkdownSection:
        knowledge_table = 'None available...'
        # Display knowledge learned
        if self.orchestrator.memory.knowledge:
            knowledge_table = MarkdownTable(title='', columns = [
                "Category",
                "Key",
                "Value",
                "Confidence",
            ])
            for item in self.orchestrator.memory.knowledge[:10]:  # Show first 10
                knowledge_table.add_row([
                    item.category,
                    item.key[:30] + "..." if len(item.key) > 30 else item.key,
                    str(item.value)[:50] + "..."
                    if len(str(item.value)) > 50
                    else str(item.value),
                    f"{item.confidence:.2f}",
                ])

        return self.add_section("🧠 Knowledge Extracted", [knowledge_table])

    async def get_token_usage(self) -> MarkdownSection:
        """Display the token usage, if available."""
        summary_info = ["Token usage not available"]
        if deep_search.token_counter:
            summary = await deep_search.token_counter.get_summary()
            if summary and hasattr(summary, "usage"):
                summary_info = [f"* Total Tokens: {summary.usage.total_tokens}"]
                if hasattr(summary, "cost"):
                    summary_info.append(f"* Total Cost: ${summary.cost:.4f}")

        return self.add_section("Total Tokens", summary_info)

    def get_workspace_artifacts(self) -> MarkdownSection:
        """Display workspace artifacts if any were created."""
        artifacts_info = ["Workspace artifacts usage not available"]
        if self.orchestrator.memory.artifacts:
            artifacts_info = ["📁 Artifacts Created:"]
            for name in list(self.orchestrator.memory.artifacts.keys())[:5]:
                artifacts_info.append(f"* {name}")

        return self.add_section("📁 Artifacts Created", artifacts_info)

    def get_final_data(self) -> list[MarkdownSection]:
        """
        Returns the list of Markdown sections for the final data, but they are also
        added to the whole document, so you can also just print the whole thing.
        """
        self.monitor.update_execution_time()
        return [
            self.get_final_statistics(),
            self.get_budget_summary(),
            self.get_knowledge_summary(),
            self.get_token_usage(),
            self.get_workspace_artifacts(),
        ]

async def markdown_main(
    args: argparse.Namespace, 
    config: DeepOrchestratorConfig,
    deep_search: DeepSearch):

    if args.noop:
        print(f"Inside markdown_main. Returning...")
        return

    mcp_app = await deep_search.setup()

    monitor = MarkdownDeepOrchestratorMonitor(deep_search.orchestrator)

    display = MarkdownDisplay("Deep Research Agent for Finance", 
        deep_search, deep_search.orchestrator, monitor)

    # Update display in background
    async def update_loop():
        while True:
            try:
                doc = display.update()
                print(doc)
                await asyncio.sleep(10.0)
            except Exception as e:
                mcp_app.logger.error(f"Display update error: {e}")
                break

    # Start update loop
    update_task = asyncio.create_task(update_loop())

    results = {}
    try:
        results = await deep_search.run()
    finally:
        # Final update
        doc = display.update()
        print(doc)
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass
    
    def truncate(n: int, s: str) -> str:
        return s[:n] + "..." if len(s) > n else s

    # Show the research results
    research_results = ''
    if results.get('research'):
        research_results = truncate(5000, results['research'])
    else:
        research_results = "No research results!!"

    mcp_app.logger.info(research_results)
    fr = display.add_financial_results(research_results)
    

    excel_results = ''
    if results.get('excel'):
        excel_results = truncate(5000, results['excel'])
    else:
        excel_results = "No excel results!!"

    mcp_app.logger.info(excel_results)
    er = display.add_excel_results(excel_results)

    for section in display.get_final_data():
        print(section)

    if args.output_path:
        with open(f"{args.output_path}/results.markdown", 'w') as file:
            file.write(str(display))

    final_msg = f"Final results and app statistics written to {args.output_path}/results.markdown"
    print(final_msg)
    mcp_app.logger.info(final_msg)

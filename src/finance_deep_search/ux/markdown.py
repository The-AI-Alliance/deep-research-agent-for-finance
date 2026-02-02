#!/usr/bin/env python
"""
The Markdown-formatted streaming output version of Deep Orchestrator Finance Research Example
"""
# Allow types to self-reference during their definitions.
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timedelta
from json.decoder import JSONDecodeError
from typing import cast, Callable, Generic

from mcp_agent.workflows.deep_orchestrator.orchestrator import DeepOrchestrator
from openai.types.chat import ChatCompletionMessage
from anthropic.types import Message

from common.string_utils import MarkdownUtil, clean_json_string
from common.deep_search import DeepSearch, BaseTask, GenerateTask, AgentTask, TaskStatus
from ux import Display
from ux.markdown_elements import (
    MarkdownElement,
    MarkdownSection,
    MarkdownTable,
    MarkdownTree)


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
                step_node = completed.add(f"{step.description[:60]}...")
                # Show first 3 tasks if many, otherwise all
                tasks_to_show = step.tasks[:3] if len(step.tasks) > 3 else step.tasks
                for task in tasks_to_show:
                    if task.status == "completed":
                        icon = "✓"
                    elif task.status == "failed":
                        icon = "✗"
                    else:
                        icon = "•"
                    step_node.add(f"{task.description[:40]}...")
                if len(step.tasks) > 3:
                    step_node.add(f"... +{len(step.tasks) - 3} more tasks")

        # Current/Active step - prioritize showing active and failed tasks
        current_step = queue.get_next_step()
        if current_step:
            active = tree.add("▶ Active Step")
            active_node = active.add(f"{current_step.description[:60]}...")

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
                    icon = "⟳"
                elif task.status == "failed":
                    icon = "✗"
                elif task.status == "completed":
                    icon = "✓"
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
                        f"... +{remaining} more ({', '.join(parts)})"
                    )

        # Pending steps (just count)
        if queue.pending_steps:
            _pending = tree.add(f"⏳ {len(queue.pending_steps)} Pending Steps")

        # Failed tasks summary if any
        if queue.failed_task_names:
            failed = tree.add(f"❌ {len(queue.failed_task_names)} Failed Tasks")
            for task_name in list(queue.failed_task_names)[:2]:
                failed.add(f"{task_name}")

        # Queue summary
        tree.add(f"📊 {queue.get_progress_summary()}")

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
                status = "✓ Done"
            elif step == queue.get_next_step():
                status = "→ Active"
            else:
                status = "Pending"

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
                    lines.append(f"Total Tokens: {usage.total_tokens:,}")
                    lines.append(f"Input Tokens: {usage.input_tokens:,}")
                    lines.append(f"Output Tokens: {usage.output_tokens:,}")

                    # Cost if available
                    if hasattr(summary, "cost"):
                        lines.append(
                            f"Estimated Cost: ${summary.cost:.4f}"
                        )

                    # Get top consumers
                    node = counter.find_node(self.orchestrator.name)
                    if node and node.children:
                        lines.append("\nTop Consumers:")
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
            lines.append("]No token usage data available yet")

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

    def get_status_summary_content(self) -> (MarkdownTable, MarkdownSection):
        """Get overall status summary as a Markdown table and other content."""
        self.update_execution_time()

        table = MarkdownTable(title="📊 Status", 
            columns=[('Quantity', 'left'),('Value', 'right')])
        table.add_row(["Objective", f"{self.orchestrator.objective[:100]}..."])
        table.add_row(["Iteration", self.orchestrator.iteration/self.orchestrator.config.execution.max_iterations])
        table.add_row(["Replans",   self.orchestrator.replan_count/self.orchestrator.config.execution.max_replans])
        table.add_row(["Elapsed",   self.execution_time])

        content = [
            "The _full objective_ abbreviated in the table above is shown next.",
            "Note that `{{foo}}` strings are part of the prompt that were replaced with appropriate values, e.g., `{{ticker}}` is replaced with the ticker symbol.",
            "\n",
        ]
        content.extend([f"> {line}" for line in self.orchestrator.objective.split('\n')])
        content.extend(["\n", "(End of the objective listing...)"])
        objective = MarkdownSection(title="Full Objective", content=content)
        return (table, objective)

    def update_execution_time(self) -> timedelta:
        self.end_time = time.time()
        self.execution_time = self.end_time - self.start_time
        return self.execution_time


class MarkdownDisplay(Display[DeepSearch]):
    def __init__(self, 
        title: str,
        system: DeepSearch,
        update_iteration_frequency_secs: float = 1.0,
        variables: dict[str, any] = {}):
        super().__init__(title, system, update_iteration_frequency_secs, variables)
        self.print_on_update: bool = variables.get('print_on_update', True)
        output_path = variables['output_path']
        ticker = variables['ticker']
        self.research_results_file = output_path / f"{ticker}_report.markdown"

        self.orchestrator = self.system.orchestrator
        self.monitor = MarkdownDeepOrchestratorMonitor(self.orchestrator)
        self.layout = MarkdownDisplay.__make_layout(title, self.system.properties())

    def __make_layout(title: str, properties: dict[str,any]) -> MarkdownSection:
        layout = MarkdownSection(title=title)
        
        # Make a Markdown table of the runtime properties. First wrap the keys in `...`
        # to render as fixed-width/code font.
        top_table = MarkdownTable("This run's properties", ['Property', 'Value'])
        for key, value in properties.items():
            top_table.add_row([f"`{key}`", value])
        layout.add_intro_content([top_table])

        # Main structure
        layout.add_subsections({
            "top_section": MarkdownSection(title="App Runtime Stats"),
            "botton_section": MarkdownSection(title="Financial Results"),
        })

        # Top section - queue, plan, and memory
        layout["top_section"].add_subsections({
            "queue": MarkdownSection(title="Task Queue"),
            "plan": MarkdownSection(title="Current Plan"),
            "memory": MarkdownSection(title="Memory"),
        })

        # Bottom section - budget, status, and agents, and final results added later.
        layout["botton_section"].add_subsections({
            'budget': MarkdownSection(title="💰 Runtime Budget Statistics"),
            'status': MarkdownSection(title="📊 Status Summary"),
            'policy': MarkdownSection(title="⚙️ Policy Engine"),
        })
        return layout

    async def run_live(self, function: Callable[[], None]):
        await function()

    def update(self) -> MarkdownSection:
        """
        Update the display with the current state. For 'behavioral' compatibility
        with the Rich UX, this method also calls print, if `self.print_on_update`
        is true.
        """
        self.monitor.update_execution_time()

        top_section = self.layout["top_section"]
        top_section["queue"].set_intro_content([self.monitor.get_queue_tree()])
        top_section["plan"].set_intro_content([self.monitor.get_plan_table()])
        top_section["memory"].set_intro_content([
            self.monitor.get_memory_table(),
            self.monitor.get_knowledge_table()])

        bottom_section = self.layout["botton_section"] 
        bottom_section["budget"].set_intro_content([self.monitor.get_budget_table()])
        summary_table, summary_obj_section = self.monitor.get_status_summary_content()
        bottom_section["status"].set_intro_content([summary_table])
        bottom_section["status"].set_subsections([summary_obj_section])
        bottom_section["policy"].set_intro_content(
            [self.monitor.get_policy_table(), self.monitor.get_agents_table()])
        
        if self.print_on_update:
            print(self.layout)
        return self.layout

    def __repr__(self) -> str:
        return str(self.layout)

    def add_section(self, title: str, 
        content: list[MarkdownElement | str] = [], 
        subsections: dict[str, MarkdownElement] = {}) -> MarkdownSection:
        section = MarkdownSection(title=title, content=content, subsections=subsections)
        self.layout.add_subsections([section])
        return section

    def __parse_json(self, s: str, context: str = '', log_failure: bool = False) -> (str, list[str]):
        try:
            # Handle an observed problem with returned results; '\\' that will cause json
            # parsing to fail.
            s2 = clean_json_string(s, '')
            obj = json.loads(s2)
            # format as nested bullets:
            mu = MarkdownUtil
            md_str = mu.to_markdown(obj, bullet='*', indent='\t', key_format='**%s:**')
            return ('', md_str)
        except (JSONDecodeError, TypeError) as err:
            err_msg = f"{err} raised while parsing attempting to parse {context} results."
            if log_failure:
                self.system.logger.warning(f"{err_msg}: input = {s}")
            return (err_msg, None)

    def __parse_openai_message(self, message_index: int, obj: any) -> list[any]:
        # For inference with OpenAI, the results will be a ChatCompletionMessage:
        def make_metadata_table(
            refusal: str,
            role: str,
            annotations: str,
            audio: str,
            function_call: str,
            tool_calls: str) -> MarkdownTable:
            table = MarkdownTable(title=f"OpenAI/Ollama Reply Message #{message_index}: Metadata",
                columns = [('Item', 'left'), ('Value', 'right')])
            table.add_row(['refusal', str(refusal)])
            table.add_row(['role', str(role)])
            table.add_row(['annotations', str(annotations)])
            table.add_row(['audio', str(audio)])
            table.add_row(['function_call', str(function_call)])
            table.add_row(['tool_calls', str(tool_calls)])
            return table

        sobj = str(obj)
        content: list[any] = []
        metadata_table: MarkdownTable = None

        if isinstance(obj, ChatCompletionMessage):
            ccm: ChatCompletionMessage = cast(ChatCompletionMessage, obj)
            content = ccm.content.split('\n') if ccm.content else []
            metadata_table = make_metadata_table(
                ccm.refusal,
                ccm.role,
                ccm.annotations,
                ccm.audio,
                ccm.function_call,
                ccm.tool_calls)
        elif sobj.startswith("ChatCompletion"):
            # Is it a "str(ChatCompletion...)"? Try parsing it with the following
            #  _ugly_ hack to extract just the `content` from the string:
            try:
                s2 = re.sub(r"""ChatCompletion[^=]+\s*=\s*['"]?""", '', sobj)
                s3 = re.sub(r"""['"]?,\s*refusal\s*=.*$""", '', s2)
                content = s3.split('\n')
            except:  # bail out...
                content = sobj.split('\n')
          
        all_content: list[any] = []
        if content:
            all_content = [f"Reply Message #{message_index} Content:"]
            all_content.extend([f"> {line}" for line in content])
            all_content.extend(['\n', "(end content)"])
        if metadata_table:
            all_content.append('\n')
            all_content.append(metadata_table)

        return all_content

    def __parse_anthropic_message(self, message_index: int, obj: any) -> list[any]:
        def make_metadata_table(
            subtype: str,
            duration_ms: int,
            duration_api_ms: int,
            is_error: bool,
            num_turns: int,
            session_id: str,
            total_cost_usd: float | None = None,
            usage: dict[str, any] | None = None, 
            structured_output: any = None) -> MarkdownTable:
            table = MarkdownTable(title=f"Anthropic Reply Message #{message_index}: Metadata",
                columns = [('Item', 'left'), ('Value', 'right')])
            table.add_row(['subtype', subtype])
            table.add_row(['duration_ms', str(duration_ms)])
            table.add_row(['duration_api_ms', str(duration_api_ms)])
            table.add_row(['is_error', str(is_error)])
            table.add_row(['num_turns', str(num_turns)])
            table.add_row(['session_id', session_id])
            table.add_row(['total_cost_usd', str(total_cost_usd)])
            table.add_row(['usage', str(usage)])
            table.add_row(['total_cost_usd', str(total_cost_usd)])
            table.add_row(['structured_output', str(structured_output)])
            return table

        sobj = str(obj)
        content: list[any] = []
        metadata_table: MarkdownTable = None

        if isinstance(obj, Message):
            rm: Message = cast(Message, obj)
            content = rm.result.split('\n')
            metadata_table = make_metadata_table(
                subtype = rm.subtype,
                duration_ms = rm.duration_ms,
                duration_api_ms = rm.duration_api_ms,
                is_error = rm.is_error,
                num_turns = rm.num_turns,
                session_id = rm.session_id,
                total_cost_usd = rm.total_cost_usd,
                usage = rm.usage,
                result = rm.result,
                structured_output = rm.structured_output)
        elif sobj.startswith("Message") or sobj.startswith("ResultMessage"):
            # Try parsing it with the following _ugly_ hack to extract just the
            # `content` from the string:
            try:
                s2 = re.sub(r"""(Result)?Message\([^=]+)\s*=\s*['"]""", '', sobj)
                s3 = re.sub(r"""^.*\s*result=(.*)""", 'result:\n', s2)
                s4 = re.sub('structured_output=', '\nstructured_output:\n', s3)
                content = s4.split('\n')
            except:  # bail out...
                content = results.split('\n')

        all_content: list[any] = []
        if content:
            all_content = [f"**Message #{message_index} content:**"]
            all_content.extend([f"> {line}" for line in content])
            all_content.extend(['\n', "(end content)"])
        if metadata_table:
            all_content.append('\n')
            all_content.append(metadata_table)

        return all_content

    def __make_results_section(self, title: str, task: BaseTask) -> MarkdownSection:
        task_table = MarkdownTable(
            title=f'Task `{task.name}` Properties',
            columns=['Property', 'Value'])
        for key, value in vars(task).items():
            if key != 'result':
                task_table.add_row([key, str(value)])

        result_section = MarkdownSection(title=title, 
            content=[f"Information for task: {task.name}", task_table])
        
        if not task.result:
            result_section.add_intro_content([f"> **ERROR:** No {task.name} results! See the log file for details."])
            return result_section

        subsections: list[MarkdownSection] = []
        for i in range(len(task.result)):
            content: list[any] = []
            result = task.result[i]
            result_content = self.__parse_openai_message(i+1, result)
            if result_content:
                content.extend(result_content)
            else:
                result_content = self.__parse_anthropic_message(i+1, result)
                if result_content:
                    content.extend(result_content)
                else:
                    # Try parsing as JSON, although it probably isn't JSON...
                    (err_msg, result_content) = self.__parse_json(str(result))
                    if not result_content: # not JSON, so just split the text.
                        result_content = str(result).split('\n')
                    content.extend([f"> {line}" for line in result_content])

            ss = MarkdownSection(title=f"Reply Message #{i+1}", content=content)
            subsections.append(ss)

        result_section.add_subsections(subsections)
        return result_section


    def report_results(self, error_msg: str):
        """
        TODO: The matching of tasks to method calls for formatting is too fragile!
        """
        content = [f"See also the directory `{self.system.output_path}` for results files."]
        if error_msg:
            content.append(f"> **ERROR:** {error_msg}")
        results_section = self.add_section("Results", content=content)
        
        results_subsections = []
        for task in self.system.tasks:
            title = ''
            if task.name.find('financial') >= 0:
                title = "📊 Financial Research Result"
            elif task.name.find('excel') >= 0:
                title = "📈 Excel Creation Result"
            else:
                raise ValueError(f"Unexpected task name: {task.name}\n(tasks = {tasks})")

            s = self.__make_results_section(title, task)
            results_subsections.append(s)

        results_section.add_subsections(results_subsections)

    def _get_final_statistics(self) -> MarkdownSection:
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

    def _get_budget_summary(self) -> MarkdownSection:
        budget_summary = self.orchestrator.budget.get_status_summary()
        return self.add_section("Budget Summary", [budget_summary])

    def _get_knowledge_summary(self) -> MarkdownSection:
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

    async def _get_token_usage(self) -> MarkdownSection:
        """Display the token usage, if available."""
        summary_info = ["Token usage not available"]
        if self.system.token_counter:
            summary = await self.system.token_counter.get_summary()
            if summary and hasattr(summary, "usage"):
                summary_info = [f"* Total Tokens: {summary.usage.total_tokens}"]
                if hasattr(summary, "cost"):
                    summary_info.append(f"* Total Cost: ${summary.cost:.4f}")
        return self.add_section("Total Tokens", summary_info)

    def _get_workspace_artifacts(self) -> MarkdownSection:
        """Display workspace artifacts if any were created."""
        artifacts_info = ["Workspace artifacts usage not available"]
        if self.orchestrator.memory.artifacts:
            artifacts_info = ["📁 Artifacts Created:"]
            for name in list(self.orchestrator.memory.artifacts.keys())[:5]:
                artifacts_info.append(f"* {name}")

        return self.add_section("📁 Artifacts Created", artifacts_info)

    async def final_update(self, final_messages: list[str]) -> list[MarkdownSection]:
        """
        Prints and also returns the list of Markdown sections for the final data.
        They are also added to the whole document by the other methods called here
        and the whole document is printed to a markdown file.
        """
        self.monitor.update_execution_time()
        sections = [
            self._get_final_statistics(),
            self._get_budget_summary(),
            self._get_knowledge_summary(),
            await self._get_token_usage(),
            self._get_workspace_artifacts(),
        ]
        for section in sections:
            print(section)

        all_sections = str(self)
        with open(self.research_results_file, 'w') as file:
            file.write(all_sections)

        final_messages.append(
            f"Research results and application status data written to {self.research_results_file}.")
        for fm in final_messages:
            print(fm)
            self.system.logger.info(fm)

        return sections

    # TODO: more attributes?
    def __str__(self) -> str:
        s = super().__str__()
        return f"""MarkdownDisplay({s})"""

    @staticmethod
    def make(
        title: str,
        system: DeepSearch,
        update_iteration_frequency_secs: float = 1.0,
        variables: dict[str,any] = {}) -> MarkdownDisplay:
        """A factory method for creating instances."""
        return MarkdownDisplay(title, system, update_iteration_frequency_secs, variables)

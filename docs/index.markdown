---
layout: default
title: Home
nav_order: 10
has_children: false
---

# Deep Research Agent: Applications for Finance and Medicine

{: .tip}
> **Tip:** Use the search box at the top of this page to find specific content.

Welcome to the **The AI Alliance**: **Deep Research Agent: Applications for Finance and Medicine**. This project started as an example application of using a _deep research_ agent for financial research and recently the first version of a medical search application was added, demonstrating the universality and flexibility of the deep research approach and the underlying tool kits.   

{: .note}
> **Note:** Do you have finance, medical, or legal industry expertise? Do you have AI expertise? Do you want to grow your expertise in either area. Please join us! See our [contributing]({{site.baseurl}}/contributing) page for details.

## What Is It?

This applications use a **deep research agent** designed to collect comprehensive information from public sources and generate detailed research reports. 

The finance application targets financial analysts or investors as users, who want to research publicly-traded companies. 

The medical application targets interested "lay" people and eventually domain experts who want to do research on medical conditions, pharmaceuticals, etc. (This application is in its early stages and is very basic...)

## About

The applications leverage AI to perform automated research, analysis, and reporting. In fact, they are a _thin veneer_ over a sophisticated agent framework, [mcp-agent](https://github.com/lastmile-ai/mcp-agent){:target="mcp-agent"}, a framework for creating AI agents with Model Context Protocol (MCP) integration, from [LastMile AI](https://lastmileai.dev){:target="lastmile"}, and application library code built on top of it.

The finance research application gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

The medical research application currently uses web search only, prioritizing known-reliable sources, with plans for more in-depth searching of research portals, etc.

A legal research application is planned.

The project [`README`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance){:target="repo"} provides extensive information on running the applications, configuring them, and how to create new applications.

On our roadmap are plans to demonstrate techniques for testing AI-enabled applications, where model outputs are not _deterministic_, i.e., 100% predictable for a given set of inputs. Developers are accustomed to testing deterministic components and applications, but AI experts have the techniques developers can use to be _confident_ their AI-enabled application works as designed. See [Testing Generative AI Applications](https://the-ai-alliance.github.io/ai-application-testing/){:target="_blank"} for more on this topic.

## Try It!

The project [README](https://github.com/The-AI-Alliance/deep-research-agent-for-finance){:target="repo"} describes how to install the dependencies and run the applications.

{: .note}
> **NOTE:**
>
> Any of the `app-run-*` commands shown will invoke the inference service defined for all the applications, potentially incurring charges.

Here are some commands to try:

```shell
# For the default finance app:
make list-apps           # List the currently supported applications.

make app-help-finance    # Details on running the finance app.
make app-run-finance     # Run the finance app with default arguments.
make -n app-run-finance  # Show the command that would be run, but don't run it.

make app-medical-help    # Details on running the medical app.
make app-medical-run     # Run the medical app with default arguments.
make -n app-run-medical  # Show the command that would be run, but don't run it.

# For additional information:
make help               # General help about the make targets.
```


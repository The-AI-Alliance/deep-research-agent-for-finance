---
layout: default
title: Home
nav_order: 10
has_children: false
---

# Deep Research Agent for Finance

{: .tip}
> **Tip:** Use the search box at the top of this page to find specific content.

Welcome to the **The AI Alliance**: **Deep Research Agent for Finance**. 

{: .note}
> **Note:** Do you have finance industry expertise? Do you have AI expertise? Do you want to grow your expertise in either area. Please join us! See our [contributing]({{site.baseurl}}/contributing) page for details.

## What Is It?

This app is an example application of a **deep research agent** designed to collect comprehensive information about publicly-traded companies and generate detailed investment research reports. The target user would be a financial analyst or investor.

## About

This application leverages AI to perform automated financial research and analysis. It gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

The application is built using [mcp-agent](https://github.com/lastmile-ai/mcp-agent){:target="mcp-agent"}, a framework for creating AI agents with Model Context Protocol (MCP) integration.

We also want to demonstrate techniques for testing AI-enabled applications, where model outputs are not _deterministic_, i.e., 100% predictable for a given set of inputs. Developers are accustomed to testing deterministic components and applications, but AI experts have the techniques developers can use to be _confident_ their AI-enabled application works as designed. See [Testing Generative AI Applications](https://the-ai-alliance.github.io/ai-application-testing/){:target="_blank"} for more on this topic.

## Try It!

The project [README](https://github.com/The-AI-Alliance/deep-research-agent-for-finance){:target="repo"} describes how to install the dependencies and run this application.

{: .note}
> **NOTE:**
>
> Any of the `app-run-*` commands shown will invoke the inference service defined for all the applications, potentially incurring charges.

Here are some commands to try:

```shell
# For the default finance app:
make app-help        # Details on running the default Finance app.
make app-run         # Run the default Finance app with default arguments.
make -n app-run      # Tell make to show the command, but don't run it.

# For all the apps:
make list-apps       # List all the apps currently available.
make all-apps-help   # Details on running all the apps.

# To run a specific app:
make app-run-finance # Same as "make app-run"
make APP=finance app-run # Another way to run the finance app, specifically.

make app-run-medical # Run the medical app with default arguments
make APP=medical app-run # Another way to run the medical app, specifically.
```


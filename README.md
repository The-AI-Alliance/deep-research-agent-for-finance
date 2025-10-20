# AI in Finance Example App

A finance deep research agent designed to collect comprehensive information about publicly-traded companies and generate detailed investment research reports.

<p align="center">
<a href="https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/LICENSE.Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"/></a>
<a href="https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/LICENSE.CC-BY-4.00"><img src="https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg"/></a>
</p>

https://github.com/user-attachments/assets/60675db5-6e0a-4a8d-9463-6a0f9d0a46d7


## About

This application leverages AI to perform automated financial research and analysis. It gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

The application is built using [`mcp-agent`](https://github.com/lastmile-ai/mcp-agent), a framework for creating AI agents with Model Context Protocol (MCP) integration. The application utilizes the _deep research architecture_, described in this [AI Alliance blog post](https://thealliance.ai/blog/building-a-deep-research-agent-using-mcp-agent), which allows for the LLM to thoroughly research and revise it's findings until a comprehensive research report is complete.

See also the project [website](https://the-ai-alliance.github.io/deep-research-agent-for-finance/).

## Setup

An inference service provider or local option like Ollama is required. See **Usage** below for details.

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Install dependencies:
```bash
uv add mcp-agent
```

## Usage

In the example, the app uses `gpt4o` from OpenAI by default. If you'd like to use a model from another provider, you can edit the `mcp_agent.secrets.yaml` (see **Configuration** below) to add the API key for one of those services, then add the model you'd like to use in `mcp_agent.config.yaml`, and use the corresponding provider wrapper, i.e., `AnthropicAugmentedLLM`, in `src/finance-deep-research/main.py`, replacing the use of `OpenAIAugmentedLLM`, if you aren't using OpenAI.

Examples for specifying other providers:
- [Ollama](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/mcp_basic_ollama_agent)
- [Gemini](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/mcp_basic_google_agent)
- [All supported providers](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/)

Run the finance research agent as follows. It researches Meta, by default:

```bash
uv run src/finance_deep_search/main.py
```

An Excel spreadsheet will be written to the `output` directory.

> [!TIP]
> Run `uv run src/finance_deep_search/main.py --help` or `make app-help`
> to see the available command-line options.

The application will:
1. Connect to the configured MCP servers
2. Execute the research agent with predefined instructions
3. Generate a comprehensive stock report

> [!NOTE]
> While running the app, you may see a browser window pop up asking for permission to authenticate to a financial dataset MCP server. There is no cost to do this. You can authenticate using a `gmail` email address, for example. If you decline, the app will still run, but it may run for a longer time while the deep research agent tries to gather the information it needs without this source.

You can also use `make` to run the app. The following commands are equivalent, because `all` is the first target and its sole dependency is `app-run`:

```bash
make
make all
make app-run
```

Try `make help` or `make app-help` for additional details. (The `Makefile` also has targets that are used to develop and locally run the project website.)

### Configuration

The application uses the following configuration files:
- `mcp_agent.config.yaml` - Main configuration settings
- `mcp_agent.secrets.yaml` - API keys and secrets (_**not**_ tracked in git!).

The `mcp_agent.secrets.yaml` file is optional, as some of the keys and secrets will be read from your environment, e.g., `OPENAI_API_KEY`, if defined. See the discussion above  If you want to use this file for these definitions, copy `.venv/lib/python3.12/site-packages/mcp_agent/data/examples/basic/mcp_basic_agent/mcp_agent.secrets.yaml.example` to `mcp_agent.secrets.yaml`. (`.gitignore` already ignores `*.secrets.yaml` files.)

### Architecture

<img src="https://images.prismic.io/ai-alliance/aMCNHWGNHVfTO240_Frame162610%5B18%5D.jpg?auto=format%2Ccompress&fit=max&w=1920" alt="Deep Research Agent Architecture" width="400"/>

The source code for the [Deep Orchestrator](https://github.com/lastmile-ai/mcp-agent/tree/main/src/mcp_agent/workflows/deep_orchestrator). A detailed [AI Alliance blog post](https://thealliance.ai/blog/building-a-deep-research-agent-using-mcp-agent) on the lessons learned creating Deep Orchestrator.

High level flow:
1. **Input Processing** - Input user objective
2. **Plan Development** - Develop a full plan, with steps and subtasks
3. **Execution Phase** - Run through all steps
4. **New Verification Step** - Add an objective verification.
5. *If objective verification is not satisfied, replan and repeat*

Key components:
- **TODO Queue** - a queue of multiple steps and full plan for execution
- **Memory and Knowledge** - persisting memory and knowledge across steps. Determining when context should be fed in
- **Non-LLM functions** - Dependendency validation, MCP server validation, Agent verification
- **Replanning** - logic for triggering a new replan
- **Emergency stop** - stopping execution due to repeated failures
- **Force completion** - respecting the budget and forcing completion due to budget overrun

## Customizing Data Sources for Deep Research

The Deep Research agent for Finance integrates into data sources using MCP, which means you can customize which data sources the agent has access to. In order to add/remove certain data sources to the agent, there are two steps:

1. In `mcp_agent.config.yaml`, add the details for the MCP server you'd like to use.

Example:
```yaml
mcp:
  servers:
    yfmcp:
      command: "uvx"
      args: ["yfmcp@latest"]
    example-mcp-server:
      command: "npx"
      args: [
        "mcp-remote",
        "url-to-your-mcp-server",
        "--header",
        "Authorization: Bearer ${BEARER_TOKEN}"
      ]
```

2. In `src/finance_deep_search/main.py`, go to the config of the Deep Orchestrator and add your server as a new available server:

```python
config = DeepOrchestratorConfig(
    name="DeepFinancialResearcher",

    #add your server to the available_servers
    available_servers=["fetch", "filesystem", "yfmcp", "financial-datasets", "your-server-here"],
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
```

*[Optional] If you'd like to optimize the performance, add specific instructions to the prompt on how the model can better use your MCP data source. You will find the main prompt at `src/finance_deep_search/prompts/financial_research_agent.md`.*

## Contributing

This project is part of the AI Alliance. We welcome contributions from developers with finance industry expertise, AI expertise, or those looking to grow their skills in either area.

For contribution guidelines, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. Note that we use the "Developer Certificate of Origin" (DCO). In short, all this really requires is that you add the `-s` flag to your `git commit` commands. See [this section](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details.

### Licenses

- Code: [Apache 2.0](LICENSE.Apache-2.0)
- Documentation: [Creative Commons Attribution 4.0 International](LICENSE.CC-BY-4.0)
- Data: [Community Data License Agreement - Permissive - Version 2.0](LICENSE.CDLA-2.0)

## About the GitHub Pages Website Published from this Repo

The project's [companion website](https://the-ai-alliance.github.io/deep-research-agent-for-finance/) is published using [GitHub Pages](https://pages.github.com/), where the pages are written in Markdown and served using [Jekyll](https://github.com/jekyll/jekyll).

The [`docs`](tree/main/docs) folder contains the website sources. There are `Makefile` targets running the website locally. Try `make help` for details.

The repo root directory has several files and subdirectories that are part of the website implementation, include the following:

* [`docs`](tree/main/docs): The sources (Markdown, JavScript, CSS, etc.) for the web site.
* [`GITHUB_PAGES.md`](tree/main/GITHUB_PAGES.md): Details about the website, how to edit it, and how to run it locally for previewing.
* [`check-external-links.sh`](tree/main/check-external-links.sh): Our convention is that links to external URLs should have a `target` defined (e.g., `target="_blank"`) to open a new browser tab or window. This script checks for missing targets.
* [`Gemfile`](tree/main/Gemfile): Ruby library dependencies for the Jekyll website.

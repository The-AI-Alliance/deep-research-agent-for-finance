# Deep Research Agent for Finance: An Example Application Using AI Agents in Finance

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

An account with OpenAI or Anthropic is required, or you can use a local option like Ollama. Those are the three supported model inference options, currently. See [Usage](#usage) below for details. (Other inference options are planned; see also [Configuration](#configuration) below.)

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Install dependencies. We recommend using [`uv`](https://docs.astral.sh/uv/), but you can use alternative Python package manages that work with `pyproject.toml` files:
```bash
uv sync
```

<a id="usage"></a>

## Usage

The application provides several command-line options to configure the behavior:

```shell
$ cd src && uv run main_finance.py --help
usage: main_finance.py [-h] --ticker TICKER --company-name COMPANY_NAME [--reporting-currency REPORTING_CURRENCY]
                       [--output-dir OUTPUT_DIR] [--markdown-report MARKDOWN_REPORT]
                       [--output-spreadsheet OUTPUT_SPREADSHEET] [--templates-dir TEMPLATES_DIR]
                       [--financial-research-prompt-path FINANCIAL_RESEARCH_PROMPT_PATH]
                       [--excel-writer-agent-prompt-path EXCEL_WRITER_AGENT_PROMPT_PATH]
                       [--research-model RESEARCH_MODEL] [--excel-writer-model EXCEL_WRITER_MODEL]
                       [--provider {openai,anthropic,ollama}] [-u {rich,markdown}] [--temperature TEMPERATURE]
                       [--max-iterations MAX_ITERATIONS] [--short-run] [-v]

Finance Deep Research using orchestrated AI agents

options:
  -h, --help            show this help message and exit
  --ticker TICKER       Stock ticker symbol, e.g., META, AAPL, GOOGL, etc.
  --company-name COMPANY_NAME
                        Full company name
  --reporting-currency REPORTING_CURRENCY
                        The currency used by the company for financial reporting. (Default:USD)
  --output-dir OUTPUT_DIR
                        Path where Excel and other output files will be saved. (Default: ./output)
  --markdown-report MARKDOWN_REPORT
                        Path where a Markdown report is written. Ignored unless --ux markdown is used. (Default:
                        research_report.md) If the path doesn't contain a directory prefix, then the file will be
                        written in the directory given by '--output-dir'.
  --output-spreadsheet OUTPUT_SPREADSHEET
                        Path where the Excel spreadsheet is written. (Default: financials.xlsx) If the path doesn't
                        contain a directory prefix, then the file will be written in the directory given by '--
                        output-dir'.
  --templates-dir TEMPLATES_DIR
                        Path to the directory where prompt files are located. (Default: ./prompts)
  --financial-research-prompt-path FINANCIAL_RESEARCH_PROMPT_PATH
                        Path where the main research agent prompt file is located. (Default:
                        financial_research_agent.md) If the path doesn't contain a directory prefix, then the file
                        will be read in the directory given by '--templates-dir'.
  --excel-writer-agent-prompt-path EXCEL_WRITER_AGENT_PROMPT_PATH
                        Path where the Excel writer agent prompt file is located. (Default: excel_writer_agent.md)
                        If the path doesn't contain a directory prefix, then the file will be read in the directory
                        given by '--templates-dir'.
  --research-model RESEARCH_MODEL
                        The model used the research orchestrator agent. (Default: gpt-4o). It should be very
                        capable.
  --excel-writer-model EXCEL_WRITER_MODEL
                        The model used for writing results to Excel (default: o4-mini); a less powerful model is
                        sufficient.
  --provider {openai,anthropic,ollama}
                        The inference provider. Where is the model served? See the note at the bottom of this help.
                        (Default: openai)
  -u {rich,markdown}, --ux {rich,markdown}
                        The 'UX' to use. Use 'rich' for a rich console UX and 'markdown' for streaming updates in
                        markdown syntax. (Default: rich)
  --temperature TEMPERATURE
                        The 'temperature' used during inference calls to models, between 0.0 and 1.0. (Default:
                        0.7)
  --max-iterations MAX_ITERATIONS
                        The maximum number of iterations for inference/analysis passes. (Default: 10, but a lower
                        value will be used if --short-run is used. Values <= 0 will be converted to 1)
  --short-run           Sets some low maximum thresholds to create a shorter run. This is primarily a debugging
                        tool, as lower iterations, for example, means lower quality results.
  -v, --verbose         Print some extra output. Useful for some testing and debugging scenarios.

Due to current limitations, you must use either OpenAI, Anthropic, or local models served by ollama, and you have
to tell us which one using the `--provider` argument, although it defaults to 'openai'. The same provider must be
used for BOTH the orchestrator and excel writer models, so specify them accordingly. The default is 'openai', which
works for both OpenAI and Ollama, but you currently have to edit mcp_agent.config.yaml to use the correct settings!
```

The `--ticker` and `--company-name` are required.

A `Makefile` provides convenient ways to run the application, get help, etc. The `app-run` command runs the following command with the arguments shown:

```shell
cd src && uv run main.py \
    --ticker "META" \
    --company-name "Meta Platforms, Inc." \
    --reporting-currency "USD" \
    --output-dir "./output/META" \
    --markdown-report "./output/META/META_report.md" \
    --prompts-path "finance_deep_search/prompts" \
    --financial-research-prompt-path "./prompts/financial_research_agent.md" \
    --excel-writer-agent-prompt-path "./prompts/excel_writer_agent.md" \
    --research-model "gpt-4o" \
    --excel-writer-model "o4-mini" \
    --provider "openai" \
    --temperature 0.7 \
    --max-iterations 10 \
    --ux rich \
    --verbose
```

Some of these arguments are the same as the application's built-in default values.

The make target `app-run` is equivalent to `app-run-rich`, which uses the Python Rich console library as a UX. There is also a target `app-run-markdown`, which uses minimal console output and writes a Markdown report at the end. 

> [!TIP]
> * Use `make help` to see help on the most important `make` targets.
> * Use `make app-help` for specific help on running the app.

Let's go through some of the options shown. (We already discussed `--ticker` and `--company-name`.)

### Output Path

```shell
    ...
    --output-dir "./output/META"
    ...
```

Several output files, including an Excel spreadsheet of data, are written to the value passed with `--output-dir`. The application's default value is `./output`. (Actually, the full absolute path to `./output` is used.) However, the `make` target uses `./output/$TICKER`, so you can easily run the job for different companies and not clobber results for other companies.

### Markdown Report

```shell
    ...
    --markdown-report "./output/META/META_report.md"
    ...
```

Write a Markdown-formatted report at the end. This option is ignored unless `--ux markdown` is used.

### Prompt File Locations

```shell
    ...
    --prompts-path "finance_deep_search/prompts"
    --financial-research-prompt-path "financial_research_agent.md"
    --excel-writer-agent-prompt-path "excel_writer_agent.md"
    ...
```

Two prompt files are by default located in [`./src/finance_deep_search/prompts`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/finance_deep_search/prompts) (Note that the command changes directory to `src` first...):
    
* `--financial-research-prompt-path "financial_research_agent.md"` - for the research task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/finance_deep_search/prompts/financial_research_agent.md))
* `--excel-writer-agent-prompt-path "excel_writer_agent.md"` - for the Excel file writer task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/finance_deep_search/prompts/excel_writer_agent.md))

If you specify a value for either argument that includes an absolute or relative directory, then the `--prompts-path` is ignored for it.

### Models

```shell
  ...
    --research-model "gpt-4o"
    --excel-writer-model "o4-mini"
    --provider "openai"
    --temperature 0.7 
    --max-iterations 10 
  ...
```

By default, `gpt-4o` from OpenAI is used for research _orchestration_ and `o4-mini` is used for creating an Excel spreadsheet with some of the research results. If you would like to use a model from another provider, there are several options. Note that inference from OpenAI and Anthropic, and local-serving with ollama are currently supported. (However, at this time, Anthropic support hasn't been tested - help wanted!)

The `--provider` argument is a temporary implementation limitation to ensure the correct `mcp-agent` code path is followed. Our intention is to infer this automatically based on the models chosen. This also means that _you must specify two models served by the same provider._ You can't mix and match Anthropic, OpenAI, and ollama models, at this time.

In addition, at this time you have to edit [`./mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml) to uncomment the correct definition of `openai` settings. 

The `--temperature` affects the randomness of responses during inference calls. The value must be between 0.0 and 1.0. Higher temperature values yield more randomness.

The `--max-iterations` determines how many inference and checking cycles will be attempted during various stages of the agent's work. Higher values yield better results, but with more potential cost. 

An optional flag is `--short-run`, which overrides `--max-iterations` with a value of 1 and sets other limits more stringently. This is mostly a debugging tool for checking the end-to-end logic of the application, but the results are rarely research results are unlikely to be "good".

See [Configuration](#configuration) below for more details.

### The "User Experience"

```shell
...
    --verbose
    --ux rich
...
```

The `--verbose` option (used by default in the `make app-run` command), just prints some extra information at the beginning of execution (and in the optional Markdown report).

By default, a [Rich](https://rich.readthedocs.io/en/stable/introduction.html) console-based UI is used to show progress and final results. 

The alternative, `--ux markdown`, produces less console output and generates a Markdown-formatted report at the end, which is written to the value of the `--markdown-report` option discussed above. The repo contains an example from a test run of the above default command with `--ux markdown` (This command is equivalent to what `make app-run-markdown` runs). The example report is [`./output/gpt-oss_20b/META_report.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/output/gpt-oss_20b/META_report.md).

## What the Application Does

The application will:
1. Connect to the configured MCP servers
2. Execute the research agent with predefined instructions
3. Generate a comprehensive stock report

> [!NOTE]
> While running the application, you may see a browser window pop up asking for permission to authenticate to a financial dataset MCP server. There is no cost to do this. You can authenticate using a `gmail` email address, for example. If you decline, the application will still run, but it may run for a longer time while the deep research agent tries to gather the information it needs without this source.

## Architecture

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

<a id="configuration"></a>

## Configuration

There are two `mcp-agent` configuration files used:

- `mcp_agent.config.yaml` - Main configuration settings
- `mcp_agent.secrets.yaml` - API keys and secrets (_**not**_ tracked in git!).

See the [`mcp-agent` configuration docs](https://docs.mcp-agent.com/reference/configuration) for details.

> [!TIP]
> Use the tool `uvx mcp-agent config builder` to build the configuration for your `mcp-agent`-based application.

Let's begin with inference service configuration.

### Configuring the Models and Inference Service.

As discussed above, we currently require several command-line options to specify the models to use and the inference provider. You also have to edit [`./mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml) to uncomment the correct definition of `openai` settings. 

Currently, those definitions look like this, where the OpenAI inference service is chosen:

```yaml
# Since Ollama and OpenAI use the same internal code path, i.e.,
# mcp-agent's `OpenAIAugmentedLLM`, you MUST uncomment the correct "openai"
# definition here and comment out the other one!
# Eliminating this manual step is TBD.

# Use this for OpenAI inference:
openai:
  default_model: "gpt-4o-mini"
  reasoning_effort: "medium"
  base_url: "https://api.openai.com/v1"
  
# Use this for ollama inference. Change the model, too!
# openai:
#   default_model: "gpt-oss:20b"
#   reasoning_effort: "medium"
#   base_url: "http://localhost:11434/v1"
#   api_key: "ignored"

anthropic:
  default_model: "claude-3-5-sonnet-20241022"
```

To use `ollama` instead, you comment out the `openai:` configuration shown and uncomment the other one.

> [!NOTE]
> If you use ollama to serve models, pick the largest one that runs on your machine. For example, `gpt-oss:20b` works well, but requires more than 20GB of RAM. Use the same model for both research orchestration and excel spreadsheet generation. For inference through a provider like OpenAI, it makes sense to use a less costly model for the Excel spreadsheet generation step, but for local inference, this is not an issue and it is better to load and use a single model!
>
> If you use the ollama server app installed on your local machine, open the settings and enable internet access from the model, which is needed to invoke other services to gather financial information! Also select the largest cache size your chosen model(s) support.

For more details on configuring different providers that `mcp-agent` supports:

- [Ollama](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/mcp_basic_ollama_agent)
- [Gemini](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/mcp_basic_google_agent)
- [All supported providers](https://github.com/lastmile-ai/mcp-agent/tree/main/examples/model_providers/)

### Setting Up Secrets

Some settings, like API keys (e.g., `OPENAI_API_KEY`) can be read from your environment or defined in `mcp_agent.secrets.yaml` in the project root directory. _You will need this file if you don't define the required API keys and other secrets in your environment. Do not put these definitions in `mcp_agent.config.yaml`, which is managed with git._

To set up your secrets:

1. Copy the example file:
   ```bash
   cp mcp_agent.secrets.yaml.example mcp_agent.secrets.yaml
   ```

2. Edit `mcp_agent.secrets.yaml` and add your tokens:
   ```yaml
   openai:
     api_key: "your-openai-api-key"  # if using OpenAI
   
   anthropic:
     api_key: "your-anthropic-api-key"  # if using Anthropic
   ```

3. Alternatively, set environment variables:
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

> [!NOTE]
> This repo's `.gitignore` ignores `mcp_agent.secrets.yaml`, so your secrets will be **excluded** from version control. _**Do not add API keys** to `./mcp_agent.config.yaml`!_


### IBM Context Forge Integration

Production deployments of this application and other MCP-based applications should consider routing external MCP service invocations through a gateway, such as [**IBM Context Forge**](https://ibm.github.io/mcp-context-forge/), a centralized gateway that provides:

- **Unified Authentication**: Single token for all external MCP services
- **Centralized Management**: Monitor and control MCP service usage
- **Enhanced Security**: Secure proxy for external service calls
- **Consistent Access**: Standardized interface to multiple data sources

See [CONTEXT_FORGE_MIGRATION.md](CONTEXT_FORGE_MIGRATION.md) for details on using Context Forge. The instructions for configuring `mcp_agent_config.yaml` should generalize for other gateways.

## Customizing Data Sources for Deep Research

The Deep Research Agent for Finance integrates into data sources using MCP, which means you can customize which data sources the agent has access to.

### Adding External MCP Services with "Direct" Access

Use this approach if you don't need to go through a gateway, like IBM Context Forge (mentioned above). There are two steps to adding a service:

1. In `mcp_agent.config.yaml`, add the details for the MCP server you'd like to use. For example:

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

2. In `src/main.py`, around line 261, change the configuration of the Deep Orchestrator and add your server as a new available server:

```python
    # Add your server to the `available_servers`:
    config = DeepOrchestratorConfig(
        name="DeepFinancialResearcher",
        available_servers=["fetch", "filesystem", "yfmcp", "financial-datasets"],
        ...
```

Remember to add any corresponding secrets, like API keys, to `mcp_agent.secrets.yaml`.

> [!TIP]
> If you'd like to optimize the performance, add specific instructions to the prompt on how the model can better use your MCP data source. You will find the main deep-research prompt in `src/finance_deep_search/prompts/financial_research_agent.md`.

### Adding Local MCP Services

To add local MCP services:

1. In `mcp_agent.config.yaml`, add the server with direct command execution:

```yaml
mcp:
  servers:
    your-local-service:
      command: "uvx"  # or "npx" depending on the service
      args: ["your-mcp-server-package"]
```

2. Add it to `available_servers` in `src/main.py` as shown above.

See examples in `mcp_agent.config.yaml` and `src/main.py`, such as the `excel` service definition.

## Contributing to This Project

This project is maintained by [The AI Alliance](https://aialliance.org). We welcome contributions from developers with finance industry expertise, AI expertise, or those looking to grow their skills in either area. We are also making plans to create similar applications for healthcare, legal, and other domains!

For contribution guidelines, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. Note that we use the "Developer Certificate of Origin" (DCO). In short, all this really requires is that you add the `-s` flag to your `git commit` commands. See [this section](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details.

For all Alliance technical projects, see [our GitHub organization](https://the-ai-alliance.github.io/).

### Licenses

- Code: [Apache 2.0](LICENSE.Apache-2.0)
- Documentation: [Creative Commons Attribution 4.0 International](LICENSE.CC-BY-4.0)
- Data: [Community Data License Agreement - Permissive - Version 2.0](LICENSE.CDLA-2.0)

## About the GitHub Pages Website Published from this Repo

The project's [companion website](https://the-ai-alliance.github.io/deep-research-agent-for-finance/) is published using [GitHub Pages](https://pages.github.com/), where the pages are written in Markdown and served using [Jekyll](https://github.com/jekyll/jekyll).

The [`docs`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/docs) folder contains the website sources. There are `Makefile` targets running the website locally and opening the published URL:

```shell
make view-local    # Setup and run Jekyll to view the website locally.
make view-pages    # Attempt to open the published URL in a browser 
                   # or at least print the URL...
```

The repo root directory has several files and subdirectories that are part of the website implementation, include the following:

* [`docs`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/docs): The sources (Markdown, JavScript, CSS, etc.) for the web site.
* [`GITHUB_PAGES.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/docs/GITHUB_PAGES.md): Details about the website, how to edit it, and how to run it locally for previewing.
* [`check-external-links.sh`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/check-external-links.sh): Our convention is that links to external URLs should have a `target` defined (e.g., `target="_blank"`) to open a new browser tab or window. This script checks for missing targets.
* [`Gemfile`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/Gemfile): Ruby library dependencies for the Jekyll website.

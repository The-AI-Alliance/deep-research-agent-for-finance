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

> [!TIP]
> The commands shown below should be up-to-date with the code, but if a command shown doesn't work, check what's done in the `Makefile`! Please file an [issue](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/issues) or post a [discussion topic](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/discussions) if you find a mistake. Thanks...

The easiest way to run the application with default values for all optional arguments is `make app-run`. This target does some setup and then runs the command `cd src && uv run -m dra.apps.finance.main ...` where `...` is a lot of arguments. The minimum required arguments are `--ticker` and `--company-name`. So, here is the shortest command you can run to do research on Meta:

```shell
cd src && uv run -m dra.apps.finance.main --ticker META --company-name "Meta Platforms, Inc."

```

> [!NOTE]
> While running the application, you may see a browser window pop up asking for permission to authenticate to a financial dataset MCP server. This should only happen one time. There is no cost to do this. You can authenticate using a `gmail` email address, for example. If you decline, the application will still run, but it may run for a longer time while the deep research agent tries to gather the information it needs without this source.

The application provides several command-line options to configure the behavior. Use `make app-help` or `cd src && uv run -m dra.apps.finance.main --help` to see the details. Here is the output for `make app-help`:

```shell
$ make app-help
Application help provided by src/dra/apps/finance/main.py:
cd src && uv run -m dra.apps.finance.main --help
usage: main.py [-h] --ticker TICKER --company-name COMPANY_NAME
                       [--reporting-currency REPORTING_CURRENCY]
                       [--output-dir OUTPUT_DIR]
                       [--markdown-report MARKDOWN_REPORT]
                       [--output-spreadsheet OUTPUT_SPREADSHEET]
                       [--templates-dir TEMPLATES_DIR]
                       [--financial-research-prompt-path FINANCIAL_RESEARCH_PROMPT_PATH]
                       [--excel-writer-agent-prompt-path EXCEL_WRITER_AGENT_PROMPT_PATH]
                       [--markdown-yaml-header MARKDOWN_YAML_HEADER]
                       [--research-model RESEARCH_MODEL]
                       [--excel-writer-model EXCEL_WRITER_MODEL]
                       [--provider {openai,anthropic,ollama}]
                       [--temperature TEMPERATURE]
                       [--max-iterations MAX_ITERATIONS]
                       [--max-tokens MAX_TOKENS]
                       [--max-cost-dollars MAX_COST_DOLLARS]
                       [--max-time-minutes MAX_TIME_MINUTES] [--short-run]
                       [--verbose]

Finance Deep Research using orchestrated AI agents

options:
  -h, --help            show this help message and exit
  --ticker TICKER       Stock ticker symbol, e.g., META, AAPL, GOOGL, etc.
  --company-name COMPANY_NAME
                        Full company name
  --reporting-currency REPORTING_CURRENCY
                        The currency used by the company for financial
                        reporting. (Default:USD)
  --output-dir OUTPUT_DIR
                        Path where Excel and other output files will be saved.
                        (Default: ./output)
  --markdown-report MARKDOWN_REPORT
                        Path where a Markdown report is written. If empty, no
                        report is generated. (Default: research_report.md) If
                        the path doesn't contain a directory prefix, then the
                        file will be written in the directory given by '--
                        output-dir'.
  --output-spreadsheet OUTPUT_SPREADSHEET
                        Path where the Excel spreadsheet is written. (Default:
                        financials.xlsx) If the path doesn't contain a
                        directory prefix, then the file will be written in the
                        directory given by '--output-dir'.
  --templates-dir TEMPLATES_DIR
                        Path to the directory where template files are located
                        (e.g., for inference prompts). (Default: ./templates)
  --financial-research-prompt-path FINANCIAL_RESEARCH_PROMPT_PATH
                        Path where the main research agent prompt file is
                        located. (Default: financial_research_agent.md) If the
                        path doesn't contain a directory prefix, then the file
                        will be read in the directory given by '--templates-
                        dir'.
  --excel-writer-agent-prompt-path EXCEL_WRITER_AGENT_PROMPT_PATH
                        Path where the Excel writer agent prompt file is
                        located. (Default: excel_writer_agent.md) If the path
                        doesn't contain a directory prefix, then the file will
                        be read in the directory given by '--templates-dir'.
  --markdown-yaml-header MARKDOWN_YAML_HEADER
                        Path to an optional template for a YAML header to
                        write at the beginning of the Markdown report. Useful
                        for publishing the report on a GitHub Pages website.
                        Ignored if --markdown-report is empty. (Default: None)
                        If the path doesn't contain a directory prefix, then
                        the file will be read in the directory given by '--
                        template-dir'.
  --research-model RESEARCH_MODEL
                        The model used the research orchestrator agent.
                        (Default: gpt-4o). It should be very capable.
  --excel-writer-model EXCEL_WRITER_MODEL
                        The model used for writing results to Excel (default:
                        o4-mini); a less powerful model is sufficient.
  --provider {openai,anthropic,ollama}
                        The inference provider. Where is the model served? See
                        the note at the bottom of this help. (Default: openai)
  --temperature TEMPERATURE
                        The 'temperature' used during inference calls to
                        models, between 0.0 and 1.0. (Default: 0.7)
  --max-iterations MAX_ITERATIONS
                        The maximum number of iterations for
                        inference/analysis passes. (Default: 25, but a lower
                        value will be used if --short-run is used. Values <= 0
                        will be converted to 1)
  --max-tokens MAX_TOKENS
                        The maximum number of tokens for inference passes.
                        (Default: 500000, but a lower value will be used if
                        --short-run is used. Values <= 0 will be converted to
                        10000)
  --max-cost-dollars MAX_COST_DOLLARS
                        The maximum total cost in USD allowed for inference
                        calls. (Default: 2.0, but a lower value will be used
                        if --short-run is used. Values <= 0 will be converted
                        to 1.00)
  --max-time-minutes MAX_TIME_MINUTES
                        The maximum number of time in minutes allowed for
                        inference passes. (Default: 15, but a lower value will
                        be used if --short-run is used. Values <= 0 will be
                        converted to 10)
  --short-run           Sets some low maximum thresholds to create a shorter
                        run. This is primarily a debugging tool, as lower
                        iterations, for example, means lower quality results.
  --verbose             Print some extra output. Useful for some testing and
                        debugging scenarios.

Due to current limitations, you must use either OpenAI, Anthropic, or local
models served by ollama, and you have to tell us which one using the
`--provider` argument, although it defaults to 'openai'. The same provider
must be used for BOTH the orchestrator and excel writer models, so specify
them accordingly. The default is 'openai', which works for both OpenAI and
Ollama, but you currently have to edit mcp_agent.config.yaml to use the
correct settings!

TIPS:
1. Use 'make print-app-info' to see some make variables you can override.
2. Use 'make --just-print app-run' to see the arguments passed BY THIS MAKEFILE.
   Some argument values will be different in the Makefile than the hard-coded defaults
   in the application itself, which are shown in the help output above!!
3. To pass additional arguments, use 'make APP_ARGS="..." app-run'. (Note the quotes.)
```

The `--ticker` and `--company-name` are required. All other arguments are optional; they have default values that will be used. The Makefile passes all the arguments with values that are _mostly_ the same as the default values hard-coded in the application, but a few may be different. 

Here is the actual command executed by `make app-run`. (Note the use of `-n` to have `make` print the command without running it):

```shell
$ make -n app-run 
(... some setup commands elided ...)
cd src && uv run -m dra.apps.finance.main \
    --ticker "META" \
    --company-name "Meta Platforms, Inc." \
    --output-dir ".../output/finance/META" \
    --markdown-report "META_report.md" \
    --markdown-yaml-header "github_pages_header.yaml" \
    --output-spreadsheet "META_financials.xlsx" \
    --reporting-currency "USD" \
    --templates-dir "dra/apps/finance/templates" \
    --financial-research-prompt-path "financial_research_agent.md" \
    --excel-writer-agent-prompt-path "excel_writer_agent.md" \
    --research-model "gpt-4o" \
    --excel-writer-model "o4-mini" \
    --provider "openai" \
    --temperature 0.7 \
    --max-iterations 25 \
    --max-tokens 500000 \
    --max-cost-dollars 2.0 \
    --max-time-minutes 15 \
    --verbose \

echo "Output files in .../output/finance/META:"
(... listing not shown ...)
```

> [!TIP]
> * All the values for the arguments shown here are defined near the top of the `Makefile`, in the `## App defaults` section. So, if you want to change any of these values, edit the corresponding variable definitions there.
> * Use `make help` to see help on the most important `make` targets.
> * Use `make app-help` for specific help on running the app.

Let's go through some of the options shown. We already discussed `--ticker` and `--company-name`. (We won't follow the exact order shown above.)

### Output Path

```shell
    ...
    --output-dir ".../output/finance/META"
    --output-spreadsheet "META_financials.xlsx"
    ...
```

Several output files, including an Excel spreadsheet of data, are written to the value passed with `--output-dir`. The application's default value for this argument is `./output`, but the `make` target passes the absolute path to `./output/finance/$TICKER`, which makes it easier to run this job for different companies and not clobber results for other companies.

Since the `--output-spreadsheet` argument doesn't specify a directory prefix, the value for `--output-dir` will be used.

### Prompt File Locations

```shell
    ...
    --templates-path "dra/apps/finance/templates"
    --financial-research-prompt-path "financial_research_agent.md"
    --excel-writer-agent-prompt-path "excel_writer_agent.md"
    ...
```

Two prompt files are by default located in [`./src/dra/apps/finance/templates`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates) (Note that the command changes directory to `src` first, so the path is relative to `src`):
    
* `--financial-research-prompt-path "financial_research_agent.md"` - for the research task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/financial_research_agent.md))
* `--excel-writer-agent-prompt-path "excel_writer_agent.md"` - for the Excel file writer task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/excel_writer_agent.md))

If you specify a value for either prompt that includes an absolute or relative directory path, then the `--templates-path` is ignored for it. In this case, the arguments don't include directories, so the files are expected to be found in the value for `--templates-path`. 

<a id="markdown-report"></a>

### Markdown Report

```shell
    ...
    --markdown-report "META_report.md"
    --markdown-yaml-header "github_pages_header.yaml"
    ...
```

Write a Markdown-formatted report at the end. If you don't want this report generated, then use `--markdown-report ''` (empty string) or `--markdown-report None`.

Optionally, if a non-empty value is specified `--markdown-yaml-header`, then write a YAML header at the beginning of the file. This is useful if the report will be presented using GitHub Pages. The YAML header should either be a literal string or a path to a template to file read in. We use a file here: [`./src/dra/apps/finance/templates/github_pages_header.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/github_pages_header.yaml). Either way, variable definitions, e.g., `{{title}}`, will be replaced with values by the application.

Like for the spreadsheet file discussed above, the report file will be written to the output directory specified with `--output-dir`, if the file name doesn't include a directory prefix. Similarly, if the YAML header value doesn't have a directory prefix, it will be searched for in the directory specified with `--templates-dir`.

### Models and Inference Parameters

```shell
  ...
    --research-model "gpt-4o"
    --excel-writer-model "o4-mini"
    --provider "openai"
    --temperature 0.7 
    --max-iterations 25 
    --max-tokens 500000
    --max-cost-dollars 2.0
    --max-time-minutes 15
  ...
```

By default, `gpt-4o` from OpenAI is used for research _orchestration_ and `o4-mini` is used for creating an Excel spreadsheet with some of the research results. If you would like to use a model from another provider, there are several options. Note that inference from OpenAI and Anthropic, and local-serving with ollama are currently the only supported options. (However, at this time, Anthropic support hasn't been tested - help wanted!)

The `--provider` argument is a temporary implementation limitation to ensure the correct `mcp-agent` code path is followed (specifically, `OpenAIAugmentedLLM`). Eventually, we plan to infer this automatically based on the models chosen. This also means that _you must specify both models served by the same provider._ You can't mix and match Anthropic, OpenAI, and ollama models.

In addition, you have to edit [`./mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml) to uncomment the correct definition of `openai` settings and comment the other one. By default, this is what you find in that file:

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

No changes are required to this file if you use Anthropic. If you use Ollama for inference, comment out the first `openai:` block and uncommment the second. Also change the default model from `gpt-oss:20b` to whatever you are using. (These default model definitions are sometimes used for certain inference steps by `mcp-agent`, even though we explicitly specify models using command arguments, as shown above.)

See [Configuration](#configuration) below for more details on this file.

The `--temperature` affects the randomness of responses during inference calls. The value must be between 0.0 (no randomness) and 1.0 (generally too much randomness). If a values outside this range is passed, it will be reset to the nearest allowed value.

The `--max-*` arguments fine tune limits on execution:

* `--max-iterations` determines how many inference and checking cycles will be attempted during various stages of the agent's work. Higher values yield better results, but with more potential cost. 
* `--max-tokens` limits the number of inference tokens generated.
* `--max-cost-dollars` limits the money spent on inference services from OpenAI or Anthropic (It has no effect for Ollama inference).
* `--max-time-minutes` limits how many minutes the app runs.

For these arguments, passing values less than zero will be reset to "reasonable" lower bounds.

> [!NOTE]
> An optional flag is `--short-run`, which overrides `--max-*` values with smaller numbers and it sets other limits more stringently. This is primarily intended for testing and debugging to check the end-to-end logic of the application. Expect the research process to not complete successfully, as it easily hits those limits and terminates.

### The "User Experience"

```shell
...
    --verbose
...
```

The `--verbose` option (used by default in the `make app-run` command), just prints some extra information at the beginning of execution and in a few other places. It doesn't affect logging (which uses `DEBUG` by default).

A [Rich console UI](https://rich.readthedocs.io/en/stable/introduction.html) is used to show progress and final results. 

A Markdown final report is written as discussed above in [Markdown Report](#markdown-report). The repo contains an example from a test run for Meta: [`./examples/gpt-oss_20b/META_report.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/examples/gpt-oss_20b/META_report.md). there is also an example Excel spreadsheet in that directory, [`./examples/gpt-oss_20b/META_financials.xlsx`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/examples/gpt-oss_20b/META_financials.xlsx).

## What the Application Does

The application will:
1. Connect to the configured MCP servers
2. Execute the research agent with predefined instructions
3. Generate a comprehensive stock report

## Architecture

<img src="https://images.prismic.io/ai-alliance/aMCNHWGNHVfTO240_Frame162610%5B18%5D.jpg?auto=format%2Ccompress&fit=max&w=1920" alt="Deep Research Agent Architecture" width="400"/>

> [!TIP]
> See the source code for the [Deep Orchestrator](https://github.com/lastmile-ai/mcp-agent/tree/main/src/mcp_agent/workflows/deep_orchestrator) and [this detailed AI Alliance blog post](https://thealliance.ai/blog/building-a-deep-research-agent-using-mcp-agent) on the lessons learned creating Deep Orchestrator.

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

- `mcp_agent.config.yaml` - Main configuration settings. (In the GitHub repo: [`./mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml))
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

Some settings, like API keys (e.g., `OPENAI_API_KEY`) can be read from your environment or defined in `mcp_agent.secrets.yaml` in the project root directory. _You will need this file if you don't define the required API keys and other secrets in your environment. Do not put these definitions in [`mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml), which is managed with git._

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
> This repo's `.gitignore` ignores `mcp_agent.secrets.yaml`, so your secrets will be **excluded** from version control. _**Do not add API keys** to [`mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml)!_

### IBM Context Forge Integration

Production deployments of this application and other MCP-based applications should consider routing external MCP service invocations through a gateway, such as [**IBM Context Forge**](https://ibm.github.io/mcp-context-forge/), a centralized gateway that provides:

- **Unified Authentication**: Single token for all external MCP services
- **Centralized Management**: Monitor and control MCP service usage
- **Enhanced Security**: Secure proxy for external service calls
- **Consistent Access**: Standardized interface to multiple data sources

See [CONTEXT_FORGE_MIGRATION.md](CONTEXT_FORGE_MIGRATION.md) for details on using Context Forge. The instructions for configuring `mcp_agent_config.yaml` should generalize for other gateways.

## Customizing Data Sources for Deep Research

The Deep Research Agent for Finance integrates into data sources using MCP, which means you can customize which data sources the agent has access to.

### Adding External MCP Tools and Services

Let's discuss changing the tools and services used. We'll assume you are making direct access to them, versus going through a gateway, like IBM Context Forge (mentioned above). Modify the content as described for Context Forge if you are going through a gateway.

There are several steps to adding (or changing) a service:

1. In [`mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml), add the details for the MCP server. For example:

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

(These commands run local Python applications with `uvx` that connect to external services.)

2. In [`src/main.py`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/main.py), around line 215, change the configuration of the Deep Orchestrator and add your server as a new server to `available_servers`:

```python
    # Add your server to the `available_servers`:
    config = DeepOrchestratorConfig(
        name="DeepFinancialResearcher",
        available_servers=["fetch", "filesystem", "yfmcp", "financial-datasets"],
        ...
```

3. Edit the appropriate `*_agent.md` prompt templates in the [`templates`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/src/dra/apps/finance/templates) directory to tell the agent how to use this tool, including performance optimization tips. See, for example, how the main finance deep research prompt, [`src/dra/apps/finance/templates/financial_research_agent.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/src/dra/apps/finance/templates/financial_research_agent.md), provides instructions for tool use.

4. Add any corresponding secrets like API keys to `mcp_agent.secrets.yaml` or use environment variables.

5. Edit the list of tools in the prompt file YAML headers (top of the files) in `src/apps/*/templates`. Only add new tools and services that make sense for that task.

### Adding Local MCP Tools and Services

Similar to the instructions above for remote services, add local MCP tools and services similarly:

1. In [`mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/mcp_agent.config.yaml), add a tool or server with direct command execution:

```yaml
mcp:
  servers:
    your-local-service:
      command: "uvx"  # or "npx" depending on the service
      args: ["your-mcp-tool"]
```

2. Add it to `available_servers` in [`src/main.py`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/main.py) as shown above.

3. Edit the list of tools in the prompt file YAML headers (top of the files) in `src/apps/*/templates`. Only add new tools and services that make sense for that task.

An example is the `filesystem` service configured in `mcp_agent.config.yaml`, `src/main.py`, and `src/apps/finance/templates/financial_research_agent.md` for local file access.

## Contributing to This Project

This project is maintained by [The AI Alliance](https://aialliance.org). We welcome contributions from developers with domain expertise in finance, healthcare, legal, and other domains (suggestions welcome), as well as developers with AI expertise. This project is also a great opportunity for those people who want to grow their skills in either way. 

For contribution guidelines, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. Note that we use the "Developer Certificate of Origin" (DCO). In short, all this really requires is that you add the `-s` flag to your `git commit` commands. See [this section](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details.

For all Alliance technical projects, see [our GitHub organization](https://the-ai-alliance.github.io/).

### Licenses

| Asset | Licence |
| :---- | :------ |
| Code | [Apache 2.0](LICENSE.Apache-2.0) |
| Documentation | [Creative Commons Attribution 4.0 International](LICENSE.CC-BY-4.0) |
| Data | [Community Data License Agreement - Permissive - Version 2.0](LICENSE.CDLA-2.0) |

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

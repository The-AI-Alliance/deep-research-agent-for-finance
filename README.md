# Deep Research Agent: Example Applications Using AI Agents in Finance and Medicine

A deep research agent designed to collect comprehensive information about topic and generate detailed research reports. There are two applications currently:

* **Finance:** Research publicly-traded companies and generate detailed investment research reports.
* **Medicine:** Research a query on medical topics and prepare a detailed, aggregated report.

<p align="center">
<a href="https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/LICENSE.Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg"/></a>
<a href="https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/LICENSE.CC-BY-4.00"><img src="https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg"/></a>
</p>

https://github.com/user-attachments/assets/60675db5-6e0a-4a8d-9463-6a0f9d0a46d7

See also the project [website](https://the-ai-alliance.github.io/deep-research-agent-for-finance/).

## About the Applications

The applications are built using [`mcp-agent`](https://github.com/lastmile-ai/mcp-agent), a framework for creating AI agents with Model Context Protocol (MCP) integration and a common core of reusable code that makes creating new applications relatively straightforward. The application utilizes the _deep research architecture_, described in this [AI Alliance blog post](https://www.aialliance.org/blog/building-a-deep-research-agent-using-mcp-agent), which allows for the LLM to thoroughly research and revise it's findings until a comprehensive research report is complete.

### Finance

This application leverages AI to perform automated financial research and analysis. It gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

### Medicine

This more-recent application leverages AI to perform automated medical research and analysis. Based on the user query, it gathers data from multiple reliable sources to create structured reports with:

- Summary of the findings
- References to the sources of information
- Latest known practices, etc.

### Creating New Applications

See [How to Create a New Application](#how-to-create-a-new-application) below for the steps required to create a new application. We have plans to add a Legal research application soon!

## Setup

An account with OpenAI or Anthropic is required, or you can use a local option like Ollama. Those are the three supported model inference options, currently. See [Usage](#usage) and [Configuration](#configuration) below.

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

If you don't use `uv`, change the commands below and in the `Makefile` as required.

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
> While we try to keep commands listed below consistent with the current state of the code, if a command doesn't work as shown, check what is done in the `Makefile`! Of course, [issues](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/issues) or [discussion topics](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/discussions) are welcome, if you find a mistake.

The easiest way to run an application with default values for all optional arguments is `make app-run-APP`, where `APP` is currently `finance` and `medical`. `make app-run` runs the finance application, by default. 

The `app-run*` targets do some setup and then run the command `cd src && uv run -m dra.apps.APP.main ...` where `...` is a lot of arguments. 

Here are the most useful `make` targets:


| Make Target          | Description                     |
| :------------------- | :------------------------------ |
| `list-apps`          | List the known applications     |
| `app-help-finance`   | Help on the finance application |
| `app-help-medical`   | Help on the medical application |
| `app-run-finance`    | Run the finance application     |
| `app-run-medical`    | Run the medical application (see note) |

> [!NOTE]
> The medical application requires you to supply a query. Do it this way:
>```shell
> make QUERY="What are the causes of diabetes mellitus?" \
>      REPORT_TITLE="Diabetes Mellitus" app-run-medical
>```

> [!TIP]
> Run the command `make -n app-run-APP` to see what command would be executed without actually running it.

Without using make, the minimum required arguments for the finance application are `--ticker TICKER` and `--company-name COMPANY_NAME`. For the medical application, `--query "QUERY"` and `--report-title TITLE` is strongly recommended, although a generic default value will be used. (The output directory and report file name will be based on it, too.) So, for example, here is the shortest command you can run to do research on Meta:

```shell
cd src && uv run -m dra.apps.finance.main --ticker META --company-name "Meta Platforms, Inc."
```

For researching diabetes:

```shell
cd src && uv run -m dra.apps.medical.main \
  --query "What are the treatment options and the long-term prognosis for adult patients diagnosed with diabetes mellitus" \
  --report-title "Diabetes Mellitus"
```

> [!NOTE]
> While running the finance application, you may on rare occasions see a browser window pop up asking for permission to authenticate to a financial dataset MCP server. There is no cost to do this. You can authenticate using a `gmail` email address, for example. If you decline, the application will still run, but it struggle to to gather the necessary information it needs without this resource.

The applications provide many optional CLI options to configure their behaviors. Use the following `make` commands or equivalent, run the previous commands described with a `--help` flag.

Let's look at the finance application in some depth. The medical application is similar.

```shell
$ make app-help-finance      
make APP=finance app-help
Application help provided by src/dra/apps/finance/main.py:
cd src && uv run -m dra.apps.finance.main --help
usage: main.py [-h] --ticker TICKER --company-name COMPANY_NAME
               [--reporting-currency REPORTING_CURRENCY]
               [--output-dir OUTPUT_DIR] [--markdown-report MARKDOWN_REPORT]
               [--output-spreadsheet OUTPUT_SPREADSHEET]
               [--templates-dir TEMPLATES_DIR]
               [--financial-research-prompt-path FINANCIAL_RESEARCH_PROMPT_PATH]
               [--excel-writer-agent-prompt-path EXCEL_WRITER_AGENT_PROMPT_PATH]
               [--markdown-yaml-header MARKDOWN_YAML_HEADER]
               [--research-model RESEARCH_MODEL]
               [--excel-writer-model EXCEL_WRITER_MODEL]
               [--provider {openai,anthropic,ollama}]
               [--mcp-agent-config MCP_AGENT_CONFIG]
               [--temperature TEMPERATURE] [--max-iterations MAX_ITERATIONS]
               [--max-tokens MAX_TOKENS] [--max-cost-dollars MAX_COST_DOLLARS]
               [--max-time-minutes MAX_TIME_MINUTES] [--short-run] [--verbose]

Financial Deep Research using orchestrated AI agents

options:
  -h, --help            show this help message and exit
  --ticker TICKER       Stock ticker symbol, e.g., META, AAPL, GOOGL, etc.
  --company-name COMPANY_NAME
                        Full company name
  --reporting-currency REPORTING_CURRENCY
                        The currency used by the company for financial
                        reporting. (Default: USD)
  --output-dir OUTPUT_DIR
                        Path where Excel and other output files will be saved.
                        (Default: ./output)
  --markdown-report MARKDOWN_REPORT
                        Path where a Markdown report is written. If empty, no
                        report is generated. (Default:
                        finance_research_report.md) If the path doesn't
                        contain a directory prefix, then the file will be
                        written in the directory given by '--output-dir'.
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
  --mcp-agent-config MCP_AGENT_CONFIG
                        Path to the mcp_agent_config.yaml file for
                        configuration settings. (Default:
                        dra/apps/finance/config/mcp_agent.config.yaml) Specify
                        an absolute path or a path relative to the project's
                        "src" directory. See the bottom of this help for more
                        information.
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
models served by ollama, and you have to tell us which one using the '--
provider' argument. It defaults to 'openai'. The value will be used to select
the correct 'mcp_agent_config.yaml' file for configuring settings. The
mcp_agent library can also search for a 'mcp_agent.config.yaml' in the project
root directory, "./.mcp-agent", and "~/.mcp-agent/", as described in mcp-
agent's documentation. Pass '' or None as the '--mcp-agent-config' to trigger
this process.

TIPS:
1. Use 'make print-app-info' to see some make variables you can override.
2. Use 'make --just-print app-run' to see the arguments passed BY THIS MAKEFILE.
   Some argument values will be different in the Makefile than the hard-coded defaults
   in the application itself, which are shown in the help output above!!
3. To pass additional arguments, use 'make APP_ARGS="..." app-run'. (Note the quotes.)
```

The `--ticker` and `--company-name` are required. All other arguments are optional; they have default values that will be used. The `--reporting-currency` defaults to `USD`. The Makefile passes all the arguments with values that are _mostly_ the same as the default values hard-coded in the application, but a few may be different. 

Here is the actual command executed by `make app-run`. (Note the use of `-n` to have `make` print the command without running it):

```shell
$ make -n app-run-finance
(... some setup commands elided ...)
cd src && uv run -m dra.apps.finance.main \
    --ticker "META" \
    --company-name "Meta Platforms, Inc." \
    --reporting-currency "USD" \
    --output-dir "../output/finance/META" \
    --markdown-report "META_report.md" \
    --markdown-yaml-header "github_pages_header.yaml" \
    --output-spreadsheet "META_financials.xlsx" \
    --templates-dir "dra/apps/finance/templates" \
    --financial-research-prompt-path "financial_research_agent.md" \
    --excel-writer-agent-prompt-path "excel_writer_agent.md" \
    --research-model "gpt-4o" \
    --excel-writer-model "o4-mini" \
    --provider "openai" \
    --mcp-agent-config "dra/apps/finance/config/mcp_agent.config.yaml" \
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
> * All the values for the CLI arguments shown here are defined as variables near the top of the `Makefile`. So, if you want to permanently change any of these values, edit the corresponding variable definitions there.
> * Use `make help` to see a list of the most important `make` targets with brief descriptions.

Let's go through some of the options shown. We already discussed `--ticker`, `--company-name`, and `--reporting-currency`. (We won't follow the exact order shown above.)

### Output Path

```shell
    ...
    --output-dir "../output/finance/META"
    ...
```

Several output files, including a Markdown-formatted report and an Excel spreadsheet of data (discussed below), are written to the value passed with `--output-dir`. The application's default value for this argument is `./output`, but the `make` target passes the absolute path to `./output/finance/$TICKER`, which makes it easier to run this job for different companies and not clobber results for other companies.

The definition starts with `../` because the application is executed from the `src` directory and `../output` refers to a _sibling_ of `src`.

<a id="markdown-report"></a>

### Markdown Report and Spreadsheet

```shell
    ...
    --markdown-report "META_report.md"
    --markdown-yaml-header "github_pages_header.yaml"
    --output-spreadsheet "META_financials.xlsx"
    ...
```

Write a Markdown-formatted report at the end. If you don't want this report generated, then use `--markdown-report ''` (empty string) or `--markdown-report None`.

Similarly, if a non-empty value is specified for `--markdown-yaml-header`, then a YAML header block will be written at the beginning of the markdown file, using the input YAML file as a _template_ for this block. This feature is useful if the report will be presented using GitHub Pages. As shown, we are referencing the file [`./src/dra/apps/finance/templates/github_pages_header.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/github_pages_header.yaml). The file is a _template_, meaning that any variable definitions of the form `{{title}}`, will be replaced with values by the application.

The `--output-spreadsheet` argument specifies the file name for the generated spreadsheet. 

### Prompts and Other Input Files

```shell
    ...
    --templates-path "dra/apps/finance/templates"
    --financial-research-prompt-path "financial_research_agent.md"
    --excel-writer-agent-prompt-path "excel_writer_agent.md"
    ...
```

Similar to how the output files and location were specified, the two input _template_ files for this application are specified in a similarly way. They are located in [`./src/dra/apps/finance/templates`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates). (Just as for `--output-dir` above, the argument value is _relative_ to `src`, where the application is executed.)
    
* `--financial-research-prompt-path "financial_research_agent.md"` - for the deep research task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/financial_research_agent.md))
* `--excel-writer-agent-prompt-path "excel_writer_agent.md"` - for the Excel file writer task ([repo](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/templates/excel_writer_agent.md)), which creates an Excel file with some of the data gathered.

If you specify a value for either prompt that includes an absolute or relative directory path, then the `--templates-path` is ignored for it. In this case, the arguments don't include directories, so the files are expected to be found in the value for `--templates-path`. This pat is also used for the optional input Markdown YAML header mentioned in the previous section.

> [!NOTE]
> The application will verify that all input paths exist or raise an exception if not.

### Models and Inference Parameters

```shell
  ...
    --research-model "gpt-4o"
    --excel-writer-model "o4-mini"
    --provider "openai"
    --mcp-agent-config "dra/apps/finance/config/mcp_agent.config.yaml"
    --temperature 0.7 
    --max-iterations 25 
    --max-tokens 500000
    --max-cost-dollars 2.0
    --max-time-minutes 15
  ...
```

By default, `gpt-4o` from OpenAI is used for the research _orchestration_ task and `o4-mini` is used for creating an Excel spreadsheet with some of the research results. The latter task doesn't require as powerful a model. If you would like to use a model from another provider, there are several options. Note that inference from OpenAI and Anthropic, and local-serving with ollama are currently the only supported options. (However, at this time, Anthropic support hasn't been tested - help wanted!)

The `--provider` argument is used to ensure that the correct `mcp-agent` code path is followed. The same cod path is used for both OpenAI and for Ollama inference, while a separate code path is used for Anthropic. Note this means that _you must specify both models served by the same provider._ You can't mix and match Anthropic, OpenAI, and ollama models currently.

The `--mcp-agent-config` points to the correct `mcp-agent` configuration file to use, based on the `--provider` value. The example shown works for both OpenAI and Anthropic inference. If you use Ollama inference, the `Makefile` will construct this argument to be `dra/apps/finance/config/mcp_agent.config.ollama.yaml`. This is necessary because different settings have to be provided for the OpenAI code path in `mcp-agent`, compared to _actual_ OpenAI inference.

See [Configuration](#configuration) below for more details on these YAML files.

The rest of this group of arguments fine tune inference calls and budgeting. If you use OpenAI or Anthropic, you might wish to use small `--max-*` values in some cases.

The `--temperature` affects the randomness of responses during inference calls. The value must be between 0.0 (no randomness) and 1.0 (generally too much randomness), inclusive. If a values outside this range is passed, it will be reset to the nearest allowed value.

The `--max-*` arguments fine tune limits on execution:

* `--max-iterations` determines how many inference and checking cycles will be attempted during various stages of the agent's work. Higher values yield better results, but with more potential cost. 
* `--max-tokens` limits the number of inference tokens generated.
* `--max-cost-dollars` limits the money spent on inference services from OpenAI or Anthropic (It has no effect for Ollama inference).
* `--max-time-minutes` limits how many minutes the app runs. (This is loosely enforced.)

For these arguments, passing values less than zero will be reset to "reasonable" lower bounds.

> [!NOTE]
> An optional flag, which isn't shown, is `--short-run`, which overrides `--max-*` values with much smaller numbers, as well as setting other internal limits more stringently. This is primarily intended for testing and debugging to check the end-to-end logic of the application. The research process won't complete successfully, as it easily hits those limits and terminates.

### Verbosity and Output

```shell
...
    --verbose
...
```

The `--verbose` option (used by default in the `make app-run` command), just prints some extra information at the beginning of execution and in a few other places. It doesn't affect logging, which uses `DEBUG` and can be changed in the `mcp_agent.config.yaml` files discussed previously.

A [Rich console UI](https://rich.readthedocs.io/en/stable/introduction.html) is used to show progress and final results. 

A Markdown final report is written as discussed above in [Markdown Report](#markdown-report). The repo contains an example from a test run for Meta: [`./examples/gpt-oss_20b/META_report.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/examples/gpt-oss_20b/META_report.md). there is also an example output Excel spreadsheet in that directory, [`./examples/gpt-oss_20b/META_financials.xlsx`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/examples/gpt-oss_20b/META_financials.xlsx).

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

The `mcp-agent` modules uses two configuration files:

- `mcp_agent.config.yaml` - Main configuration settings. We discussed this above and the repo has several versions, e.g., [`dra/apps/finance/config/mcp_agent.config.yaml`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/config/mcp_agent.config.yaml)
- `mcp_agent.secrets.yaml` - API keys and secrets, put in the root directory of the repo or your home directory and _**not**_ tracked in git, since it contains secrets!

See the [`mcp-agent` configuration docs](https://docs.mcp-agent.com/reference/configuration) for details on these files.

> [!TIP]
> Use the tool `uvx mcp-agent config builder` to build the configuration for your `mcp-agent`-based application.

Let's begin with inference service configuration.

### More on Configuring the Models and Inference Service.

As discussed above, we currently require several command-line options to specify the models to use and the inference provider. You may also need to edit the `./mcp_agent.config.yaml` files. 

The definitions in our provided configuration files look as follows.

#### OpenAI Inference

```yaml
openai:
  default_model: "gpt-4o-mini"
  reasoning_effort: "medium"
  base_url: "https://api.openai.com/v1"
```

#### Anthropic Inference

```yaml  
anthropic:
  default_model: "claude-3-5-sonnet-20241022"
```

#### Ollama Inference

This configuration is found in the `mcp_agent.config.ollama.yaml` files in the supported applications `config` directories Note the use of `openai`!

```yaml  
openai:
  default_model: "gpt-oss:20b"
  reasoning_effort: "medium"
  base_url: "http://localhost:11434/v1"
  api_key: "ignored"
```

In our development, we primarily use `gpt-oss:20b` served by Ollama locally. If you use Ollama, you may chose a different default model. Even though the CLI lets you specify the models to use, we have observed that the default model defined here is sometimes used for various tasks, so we recommend changing this value as appropriate, too.


> [!NOTE]
> If you use `ollama` to serve models, pick the largest one that runs on your machine. For example, `gpt-oss:20b` works well, but requires more than 20GB of RAM. Use the same model for both research orchestration and excel spreadsheet generation. For inference through a provider like OpenAI, it makes sense to use a less costly model for the Excel spreadsheet generation step, but for local inference, this is not an issue and it is better to load and use a single model!
>
> If you use the `ollama` server app installed on your local machine, open the settings and enable internet access from the model, which is needed to invoke other services to gather financial information! Also select the largest cache size your chosen model(s) support.

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
> This repo's `.gitignore` ignores `mcp_agent.secrets.yaml`, so your secrets will be **excluded** from version control. _**Do not add API keys** to [`mcp_agent.config.yaml` files!_

### IBM Context Forge Integration

Production deployments of this application and other MCP-based applications should consider routing external MCP service invocations through a gateway, such as [**IBM Context Forge**](https://ibm.github.io/mcp-context-forge/), a centralized gateway that provides:

- **Unified Authentication**: Single token for all external MCP services
- **Centralized Management**: Monitor and control MCP service usage
- **Enhanced Security**: Secure proxy for external service calls
- **Consistent Access**: Standardized interface to multiple data sources

See [CONTEXT_FORGE_MIGRATION.md](CONTEXT_FORGE_MIGRATION.md) for details on using Context Forge. The instructions for configuring `mcp_agent_config.yaml` should generalize for other gateways.

<a id="customizing-data-sources-for-deep-research"></a>

## Customizing Data Sources for Deep Research

The applications integrate data sources using MCP, which means you can customize which data sources they have access to.

### Adding External MCP Tools and Services

Let's discuss changing the tools and services used. There are several steps to adding (or changing) a service:

1. In one or more of the `mcp_agent.config.yaml` files discussed above, add the details for the MCP server. For example:

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

Both of the servers shown here are accessed by running local Python applications with `uvx`, which connect to corresponding external services.

2. In `src/dra/apps/APP/main.py` (e.g., for finance, [`src/dra/apps/finance/main.py`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/apps/finance/main.py)), change the list of servers in the function `get_server_list()` near the top of the file. For the finance app, it currently looks like this:

```python
def get_server_list() -> list[str]:
    """Define the list of tools and services to use for this app."""
    return [
        "excel_writer",
        "fetch",
        "filesystem",
        "financial-datasets",
        "yfmcp",
    ]
```

3. Optionally edit the appropriate `*_agent.md` prompt templates in the `src/dra/apps/APP/templates` directories of your applications, e.g., for [finance](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/src/dra/apps/finance/templates). There are two things to edit:

  * The list of tools in the YAML header at the top of the file. Only add new tools and services that make sense for that task.
  * Describe in the prompt body how the agent should use the tool or service, including possible performance optimization tips. See, for example, how the main finance deep research prompt, [`src/dra/apps/finance/templates/financial_research_agent.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/tree/main/src/dra/apps/finance/templates/financial_research_agent.md), provides instructions for tool use.

4. Add any corresponding secrets like API keys to `mcp_agent.secrets.yaml` or use environment variables.

### Adding Local MCP Tools and Services

Similar to the instructions above for remote services, add local MCP tools and services similarly:

1. In one or more of the `mcp_agent.config.yaml files, add a tool or server with direct command execution:

```yaml
mcp:
  servers:
    your-local-service:
      command: "uvx"  # or "npx" depending on the service
      args: ["your-mcp-tool"]
```

2. Add it to the list returned by `get_server_list()` in the corresponding `main.py` file.

3. Edit the list of tools in the prompt file YAML headers (top of the files) in `src/apps/*/templates`. Only add new tools and services that make sense for that task.

See for example the `filesystem` service (for local file access) configured in the finance app's `mcp_agent.config*.yaml`, `main.py`, and `financial_research_agent.md` files.

<a id="how-to-create-a-new-application"></a>

## How to Create a New Application

With an understanding of the above discussion of the command-line interface (CLI) arguments, the configuration steps, etc., let's now discuss the steps to follow to create a new application, which we followed when we created the medical application.

As an example, let's discuss how to create a history research app. The two hardest tasks of this process are the following:

1. Finding the best, custom data sources, tools, and MCP servers for your use case.
2. Customizing the prompt(s) to effectively perform the work.

As you go through the following steps, think about these tasks.

> [!NOTE]
> We will make the core, shared code into a pip-installable library soon. For now, it is necessary to work in a fork of the git repo.

### Create the Corresponding `apps` Directory

We'll copy and edit the finance application. You might find it useful to refer to the history application, for comparison.

1. Copy `src/dra/apps/finance` to `src/dra/apps/history`.
1. Delete the `__pycache__` directory and any other obvious work files.

### Edit `src/dra/apps/history/main.py`

Start by editing the documentation comment at the top as desired.

### Configure the Tools and Services

If you know what tools and services you'll need, edit the list returned by the function `get_server_list()` at the top of the file. You'll also need to edit the definitions in `mcp_agent.config*.yaml` files in `src/dra/apps/history/config` and the prompt templates in `src/dra/apps/history/config`. The details were described above in [Customizing Data Sources for Deep Research](#customizing-data-sources-for-deep-research) above. Follow those instructions.

> [!TIP]
> To get started quickly and build your capabilities incrementally, consider starting with basic web search and file system access, the `fetch` and `filesystem` services, then add more advances services later.

#### Decide If You Need Additional "Observers"

The next function in `main.py`, `get_extra_observers()` is a "hook" for adding [`Observer`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/observer.py) instances. The app defines two (at the time of this writing...): the Rich Console display and the Markdown report generator. You might add additional observers for tracing and notification purposes. The comment for `get_extra_observers()` says the keys used can't collide with the existing observer keys, which are `display` and `markdown` for the two built-in observers.

#### Define the Application's Command-line Arguments

The next function `define_cli_arguments()` is where the CLI arguments are specified.

There are common CLI arguments, which are included with calls like `parser_util.add_arg_output_dir()` (around line 80) in `main.py`, which adds the root output directory for all generated content. You will most likely want to keep all the common CLI arguments in `main.py`. However, the order in which the arguments are setup in this function is done to group help information logically. Put the required arguments before the optional arguments. 

> [!TIP]
> Run `make app-help-finance` to see how its CLI argument definitions are reflected in the finance app's CLI.

Next decide which custom CLI arguments are required for your application. For example, the finance application has required `--ticket TICKET` and `--company-name COMPANY_NAME` CLI arguments, while the medical application has a required `--query QUERY` CLI argument. There are other custom arguments for each application, such as unique flags for the prompt templates, but they have suitable default values. 

Start by editing the `def_*` variables near the top of the function. They define default values for your custom CLI arguments. Obviously delete the old definitions for the finance application that don't apply to your use case.

Next edit the definitions of `which_app` (use `history` in this example), `app_name`, etc.

Then edit the sequence of statements to add CLI arguments, including your custom arguments. (We use Python's [`argparse`](https://docs.python.org/3/library/argparse.html#module-argparse) module.)

For example, the invocation of `parser_util.add_arg_output_dir()` uses a shared `ParserUtil` class in [`src/dra/common/utils/main.py](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/utils/main.py). Interspersed with those calls are custom argument definitions, like this one for `--ticker TICKER`:

```python
    parser_util.parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker symbol, e.g., META, AAPL, GOOGL, etc."
    )
```

We put this one first in the finance application, followed by the definition for `--company-name`, since they are the two required arguments for it.

Note that we use custom CLI arguments for the two prompt files needed by the finance application. They correspond to the two "tasks" that are executed, discussed below. Consider meaning argument names and values for the prompts you'll need. 

#### Process Custom Input and Output Paths

The `process_cli_arguments()` function calls `parser_util.process_args()`, which calls Python's `argparse.parse_arg()` function to process the user-supplied arguments.

Next there is a section where the various custom input and output paths are resolved and the input paths are confirmed to exist. The details of path resolution were discussed above in [Markdown Report](#markdown-report). That report path (the CLI argument `--markdown-report MARKDOWN_REPORT`), is added by `parser_util.add_arg_markdown_report_path()`, which was called in `define_cli_arguments()`. All such common input and output paths are resolved by `parser_util.process_args()`, so you don't need to do that yourself. You only need to add code for your custom paths, so edit the examples shown from the finance application, as required. The code comments have additional details.

#### Edit the `Variable` Definitions

The `create_variables()` function creates a dictionary passed around the application. The values are of type [`Variable`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/variables.py), each of which holds a key, a user-friendly label, and the value for the variable. `Variable` also provides tools for rendering strings from the values with appropriate formatting, such as "`value`" for code.

Because the dictionary is used for display purposes, too. Define the variables to start with the values of greatest interest to the user, such as the stock ticker symbol and company name for the finance app. 

The call to `parser_util.common_variables()` adds most of the common variables shared across applications. In the finance case, this is followed with additional custom variables. (Again the order reflects what we think is most useful for the user.)

When we discuss the prompt _template_ files below, we'll mention that you may need custom variable definitions to be substituted into the prompt templates. This is the place to define those definitions. For example, in the finance application, we do this substitution with the define `ticker` variable.

Finally, there are a number of common variables that are mostly of use for debugging and other "verbose" output, which can are added by `parser_util.only_verbose_common_vars()`. This means if user doesn't pass the `--verbose` CLI argument, these "verbose" variables won't appear in the Markdown report, etc.

After constructing the list, `create_variables()` returns a dictionary where the variable keys are used as the dictionary keys. This supports fast lookup later on.

#### Edit the Research Tasks

Next, `make_tasks()` defines the research tasks. All applications will need the first [`GenerateTask`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/tasks.py) shown, which drives the `mcp-agent` `DeepOrchestrator`. 

The finance application has a second [`AgentTask`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/tasks.py) that generates an Excel spreadsheet with results. 

Your application may only need the `GenerateTask`, but the hooks are here for more advanced uses.

Each prompt will have a prompt template file in `src/dra/apps/history/templates`. We discuss editing them next.

The bottom of `main.py` calls these functions and constructs a [`Runner`](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/src/dra/common/utils/main.py) instance, which does final component initialization and then the application is executed!

#### Edit the Prompt Template(s)

_Prompt engineering_ is an art form, requiring experimentation and incremental refinement to get the best results. Unfortunately, prompts usually have to be tailored for specific models. We assume that the same prompt templates work for any inference model choices, but this assumption may not work for you.

Previously we said you need to define the CLI arguments for your prompt templates (at least one for the main `GenerateTask`). Edit the file name(s) as desired and then edit the prompt files. The finance application prompt templates are good examples of non-trivial prompts.

We say _templates_, because you will find "variables" defined in the files like this: `{{key}}`, where `key` is expected to be found in the `Variables` dictionary discussed above. Hence, you will want to define any variables in the `create_variables()` function that you will need replaced in the prompts at runtime.

### Edit the `mcp_agent.config*.yaml` Files

You may have already done this in the step above to define the servers you need, but make sure no additional changes are required. For example, you might want to change the default models used for the inference providers defined.

### Add your Application to the Makefile

Currently the `Makefile` knows about the two applications for `finance` and `medical`. For example, the following convenient make targets are there:

| Make Target          | Description                     |
| :------------------- | :------------------------------ |
| `list-apps`          | List the known applications     |
| `app-help-finance`   | Help on the finance application |
| `app-help-medical`   | Help on the medical application |
| `app-run-finance`    | Run the finance application     |
| `app-run-medical`    | Run the medical application (see note) |

> [!NOTE]
> The medical application requires you to supply a query. Do it this way:
>```shell
> make QUERY="What are the causes of diabetes mellitus?" app-run-medical
>```

Make the following changes to add support for the history application:

* Define `HISTORY_APP` and add it to the definition of `APPS`.
* Find the `# For the Finance app:` section and add a new one below it for the history application. Define any custom variables and values that will be use for running the command with your preferred CLI arguments.
* In `# For all apps:` add a new `else ifeq...` clause, or just rely on the default `else` definition:

```
else ifeq (history,${APP})
  OUTPUT_DIR              ?= ../output/${APP}/something
  OUTPUT_REPORT           ?= something_report.md
```
* In `# Application-specific run commands:` copy and paste the `do-app-run-finance` definition, rename it to `do-app-run-history` and edit the command as desired.

Check that the following commands work:

```shell
make list-apps           # Does "history" appear?
make app-help-history    # Is the history app's help and other content shown?
make -n app-run-history  # Is the app's command shown (but not executed)?
make app-run-history     # Does the app run successfully?
```

### Save to Git

Of course, don't forget to save your work in git...

### Submit a PR?

Consider contributing your application back to the project! The next section discusses getting involved.

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

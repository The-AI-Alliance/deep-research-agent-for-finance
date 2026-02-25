# Deep Research Agent for Medical Research

This README adds additional information to supplement the description provided in the repo's main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/README.md). See that README for required tools, including `uv` and `npm`.

<a id="usage"></a>

## Usage

> [!TIP]
> While we try to keep commands listed below consistent with the current state of the code, if a command doesn't work as shown, check what is done in the `Makefile`! Of course, [issues](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/issues) or [discussion topics](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/discussions) are welcome, if you find a mistake.

The main MCP server used by the medical application has to be installed locally first.

### Installing `medical-mcp`

The [`medical-mcp`](https://github.com/JamesANZ/medical-mcp) MCP server runs locally on your machine and it does most of the searching for this application's deep research. While most Node- and Python-based MCP servers can be installed and run automatically using `npx` or `uvx`, respectively, this one apparently can't be run that way.

#### Install the Node Module

Node (with `npm` and `npx`) should already be installed, as they were listed as requirements in the project [README](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/README.md).

Use the following command to install `medical-mcp` or see the `medical-mcp` [README](https://github.com/JamesANZ/medical-mcp) for other options.

```shell
npm install -g medical-mcp
``` 

Next, determine where this module is installed, as you may need to change a path in the `mcp_agent.config*.yaml` files for the medical application.

If you installed `node` using [HomeBrew](https://brew.sh/) on MacOS or Linux, then try the following commands:

```shell
echo $HOMEBREW_HOME
ls -l $HOMEBREW_HOME/lib/node_modules/medical-mcp/build/index.js
```

If the file exists _and_ `HOMEBREW_HOME` is set to `/opt/homebrew`, you can skip the rest of this section and go to **A Note about the Prompt Template File**.

If the `ls` command found the file, but `HOMEBREW_HOME` is not set to `/opt/homebrew` (`/usr/local/homebrew` is one possibility...), then jump a few paragraphs to where we tell you edit the YAML files and just change the path to `build/index.js` to match your path, as shown by the `ls -l` command.

If you didn't install `node` with HomeBrew or you are on Windows, then do the following. Use the `which npm` command on MacOS or Linux, or `where npm` on Windows to determine where `npm` is installed. 

As an example, suppose the command returns `$HOME/mytools/node/bin/npm`. The `medical-mcp` library will be installed in `$HOME/mytools/node/lib/node_modules/medical-mcp/`. Under this directory will be a file `build/index.js`, i.e., `$HOME/mytools/node/lib/node_modules/medical-mcp/build/index.js`. This is the path you need to use in the `mcp_agent.config*.yaml` files.

Finally, edit the medical configuration YAML files, `mcp_agent.config*.yaml`, in [`apps/src/dra/medical/config`](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/apps/src/dra/medical/config). Find the configuration for `medical-mcp` in each one and change the path in the `args:` line to match your path. Here is the default setting:

```yaml
medical-mcp:
  command: "node"
  "args": ["/opt/homebrew/lib/node_modules/medical-mcp/build/index.js"]
```

### A Note about the Prompt Template File

The prompt template file [`medical_research_agent.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/apps/src/dra/medical/templates/medical_research_agent.md) tells the model how to use this MCP Server for different kinds of user queries. This is instructive to read if you try other MCP servers. Similarly, the prompt template files for the finance application also provide guidance for use of the MCP servers configured for it.

### Make Targets for Running the Application and Related Tasks

Finally we are ready to run the application. The easiest way to run it with default values for all optional arguments is `make app-run-medical`.

The `app-run-medical` target does some setup and then runs the command `cd src && uv run -m dra.apps.medical.main ...` where `...` is a lot of arguments. 

Here are the most useful `make` targets for this application:

| Make Target          | Description                     |
| :------------------- | :------------------------------ |
| `list-apps`          | List all the applications.      |
| `app-help-medical`   | Help on the medical application |
| `app-run-medical`    | Run the medical application. Prompts you for a research query and a report title. |

> [!NOTE]
> The application can run for a long time! If you want to limit it to a short run to see what it does (with less than optimal results...), try this instead:
>
> ```shell
> make APP_ARGS=--short-run app-run-medical
> ```

Either running with or without `make`, the required arguments for the medical application are `--query "QUERY"`, `--terms "TERMS`, and `--report-title "TITLE"`, but you will be prompted for them if you don't supply the arguments.

As an example, here is an example of the shortest `make` and CLI commands you can run to do research with a custom query about _diabetes mellitus_:

```shell
make QUERY="What are the causes of diabetes mellitus?" \
    REPORT_TITLE="Diabetes Mellitus" \
    TERMS="diabetes,insulin,pancreas" \
    app-run-medical

cd src && uv run -m dra.apps.medical.main \
    --query "What are the causes of diabetes mellitus?" \
    --report-title "Diabetes Mellitus" \
    --terms "diabetes,insulin,pancreas"
```

The application provides many optional CLI arguments to configure its behavior. Use the following `make` and CLI commands to see the help.

```shell
$ make app-help-medical
make APP=medical app-help
Application help provided by apps/src/dra/medical/main.py:
cd src && uv run -m dra.apps.medical.main --help
usage: main.py [-h] [-q QUERY] [--markdown-report MARKDOWN_REPORT]
               [--report-title REPORT_TITLE] [--output-dir OUTPUT_DIR]
               [--templates-dir TEMPLATES_DIR]
               [--medical-research-prompt-path MEDICAL_RESEARCH_PROMPT_PATH]
               [--markdown-yaml-header MARKDOWN_YAML_HEADER]
               [--research-model RESEARCH_MODEL]
               [--provider {openai,anthropic,ollama}]
               [--mcp-agent-config MCP_AGENT_CONFIG]
               [--temperature TEMPERATURE] [--max-iterations MAX_ITERATIONS]
               [--max-tokens MAX_TOKENS] [--max-cost-dollars MAX_COST_DOLLARS]
               [--max-time-minutes MAX_TIME_MINUTES] [--short-run] [--verbose]

Medical Deep Research using orchestrated AI agents

options:
  -h, --help            show this help message and exit
  -q QUERY, --query QUERY
                        A quoted string with your research query. If not
                        provided on the command line, you will be prompted for
                        it.
  --markdown-report MARKDOWN_REPORT
                        Path where a Markdown report is written. If empty, a
                        file name will be generated from the report title.
                        (Default: medical_research_report.md) If the path
                        doesn't contain a directory prefix, then the file will
                        be written in the directory given by '--output-dir'.
  --report-title REPORT_TITLE
                        A concise title to use for the report. If None, you
                        will be prompted to input it.
  --output-dir OUTPUT_DIR
                        Path where Excel and other output files will be saved.
                        (Default: ./output)
  --templates-dir TEMPLATES_DIR
                        Path to the directory where template files are located
                        (e.g., for inference prompts). (Default: ./templates)
  --medical-research-prompt-path MEDICAL_RESEARCH_PROMPT_PATH
                        Path where the main research agent prompt file is
                        located. (Default: medical_research_agent.md) If the
                        path doesn't contain a directory prefix, then the file
                        will be read in the directory given by '--templates-
                        dir'.
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
  --provider {openai,anthropic,ollama}
                        The inference provider. Where is the model served? See
                        the note at the bottom of this help. (Default: openai)
  --mcp-agent-config MCP_AGENT_CONFIG
                        Path to the mcp_agent_config.yaml file for
                        configuration settings. (Default:
                        dra/apps/medical/config/mcp_agent.config.yaml) Specify
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
agent's documentation. Pass '' or None as the '--mcp-agent-config' value to
have `mcp-agent` search these directories instead.

TIPS:
1. Use 'make print-app-info' to see some make variables you can override.
2. Use 'make --just-print app-run' to see the arguments passed BY THIS MAKEFILE.
   Some argument values will be different in the Makefile than the hard-coded defaults
   in the application itself, which are shown in the help output above!!
3. To pass additional arguments, use 'make APP_ARGS="..." app-run'. (Note the quotes.)

```

Most of the arguments are shared between the applications, so they are discussed
in the main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/README.md).

This help output was generated by passing `--help` to the command itself, e.g.,:

```shell
cd src && uv run -m dra.apps.medical.main --help
```

Note that for the optional arguments, default values are shown. _These are the defaults built into the application itself,_ which will sometimes be different than the values explicitly passed to the command in the `Makefile`. To see these values easily, use the following command, where the `-n` argument tells `make` to echo commands, but don't run them:

```shell
$ make -n app-run-medical
...
cd src && uv run -m dra.apps.medical.main \
    --query "" \
    --report-title "" \
    --output-dir "../output/medical" \
    --markdown-yaml-header "github_pages_header.yaml" \
    --templates-dir "dra/apps/medical/templates" \
    --medical-research-prompt-path "medical_research_agent.md" \
    --research-model "gpt-4o" \
    --provider "openai" \
    --mcp-agent-config "dra/apps/medical/config/mcp_agent.config.yaml" \
    --temperature 0.7 \
    --max-iterations 25 \
    --max-tokens 500000 \
    --max-cost-dollars 2.0 \
    --max-time-minutes 15 \
    --verbose 
...
```

> [!TIP]
> * All the values for the CLI arguments shown here are defined as variables near the top of the `Makefile`. So, if you want to permanently change any of these values, edit the corresponding variable definitions there.
> * Use `make help` to see a list of the most important `make` targets with brief descriptions.

The unique options for the medical application include the `--query` and `--report-title`. We pass an empty string in the `Makefile`, so you will be prompted for them. 

There is also a `--markdown-report` option that specifies the report's file name. The `Makefile` doesn't use this argument for the medical application (it does for the finance application...). Instead, it allows the application to synthesize a suitable name based on the report title you specify. However, it will be written in the `--output-dir` location, so you can find it easily.

Finally, `--medical-research-prompt-path`, is also unique to this app. It is the path to the prompt template file. The default value for this path is `medical_research_agent.md`. Because a directory path isn't specified, this file will be searched for in the value passed with `--templates-dir`, which defaults to `dra/apps/medical/templates`.

See [`examples/gpt-oss_20b/diabetes_report.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/examples/gpt-oss_20b/diabetes_report.md) for a sample report.

## Customizing Data Sources for Medical Deep Research

Much of the world's important medical information is behind paywalls. As an open-source demo application, we can only use freely-accessible data sources. If you have accounts to sources behind paywalls, you can add them to the application following the instructions in the main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/README.md). Also, many datasets, research paper portals, etc. don't provide MCP server access, so other means are necessary.

The list of resources we are investigating is maintained in this project [issue](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/issues/48). Help wanted!


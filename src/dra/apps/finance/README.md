# Deep Research Agent for Finance

This README adds additional information to supplement the description provided in the repo's main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/README.md).

<a id="usage"></a>

## Usage

> [!TIP]
> While we try to keep commands listed below consistent with the current state of the code, if a command doesn't work as shown, check what is done in the `Makefile`! Of course, [issues](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/issues) or [discussion topics](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/discussions) are welcome, if you find a mistake.

The easiest way to run the application with default values for all optional arguments is `make app-run-finance`. (There is a `make app-run` target, but it runs the finance application, by default.) 

The `app-run-finance` target does some setup and then runs the command `cd src && uv run -m dra.apps.finance.main ...` where `...` is a lot of arguments. 

Here are the most useful `make` targets for this application:


| Make Target          | Description                     |
| :------------------- | :------------------------------ |
| `list-apps`          | List all the applications.      |
| `app-help-finance`   | Help on the finance application |
| `app-run-finance`    | Run the finance application. Uses META by default. |

> [!NOTE]
> For easy demonstration purposes, default definitions for the required flags in the `Makefile` allow `app-run-finance` to execute without providing any flags.

Without using make, the minimum required arguments for the finance application are `--ticker TICKER` and `--company-name COMPANY_NAME`.

So, for example, here are the shortest `make` and CLI commands you can run to do research on IBM:

```shell
$ make TICKER=IBM COMPANY_NAME="International Business Machines Corporation" app-run-finance

$ cd src && uv run -m dra.apps.finance.main --ticker IBM --company-name "International Business Machines Corporation"
```

The application provides many optional CLI options to configure its behavior. They are discussed in the main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/README.md).

## Customizing Data Sources for Finance Deep Research

Much of the important finance information is behind paywalls. As an open-source demo application, we can only use freely-accessible data sources. If you have accounts to sources behind paywalls, you can add them to the application following the instructions in the main [README](https://github.com/The-AI-Alliance/deep-research-agent-for-finance/blob/main/README.md). 

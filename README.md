# AI in Finance Example App

A finance deep research agent designed to collect comprehensive information about publicly-traded companies and generate detailed investment research reports.

## About

This application leverages AI to perform automated financial research and analysis. It gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

The application is built using [mcp-agent](https://github.com/lastmile-ai/mcp-agent), a framework for creating AI agents with Model Context Protocol (MCP) integration.

See also our [website](https://the-ai-alliance.github.io/ai-in-finance-example-app/).

## Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-in-finance-example-app
```

2. Install dependencies:
```bash
uv add mcp-agent
```

## Usage

Currently, the app requires an OpenAI or Anthropic account. Edit `mcp_agent.secrets.yaml` to add the API key for one of those services.

Run the finance research agent:

```bash
uv run main.py
```

The application will:
1. Connect to the configured MCP servers
2. Execute the research agent with predefined instructions
3. Generate a comprehensive stock report

You can also run `make`, which builds the default `all` target, which builds the `run-app` target to run the app. In other words, the following are equivalent:

```bash
make
make all
make run-app
```

Try `make help` for additional details.

### Configuration

The application uses configuration files:
- `mcp_agent.config.yaml` - Main configuration settings
- `mcp_agent.secrets.yaml` - API keys and secrets (not tracked in git)

## Contributing

This project is part of the AI Alliance. We welcome contributions from developers with finance industry expertise, AI expertise, or those looking to grow their skills in either area.

For contribution guidelines, see the AI Alliance [CONTRIBUTING](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md) instructions. Note that we use the "Developer Certificate of Origin" (DCO). In short, all this really requires is that you add the `-s` flag to your `git commit` commands. See [this section](https://github.com/The-AI-Alliance/community/blob/main/CONTRIBUTING.md#developer-certificate-of-origin) for details.

### Licenses

- Code: [Apache 2.0](LICENSE.Apache-2.0)
- Documentation: [Creative Commons Attribution 4.0 International](LICENSE.CC-BY-4.0)
- Data: [Community Data License Agreement - Permissive - Version 2.0](LICENSE.CDLA-2.0)

## About the GitHub Pages Website Published from this Repo

The website is published using [GitHub Pages](https://pages.github.com/), where the pages are written in Markdown and served using [Jekyll](https://github.com/jekyll/jekyll). 

There are `Makefile` targets running the website locally. Try `make help` for details.


See [GITHUB_PAGES.md](GITHUB_PAGES.md) for more information.

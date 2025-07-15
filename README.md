# AI in Finance Example App

A finance deep research agent designed to collect comprehensive information about publicly traded companies and generate detailed investment research reports.

## About

This application leverages AI to perform automated financial research and analysis. It gathers data from multiple reliable financial sources to create structured investment reports with:

- Basic stock information and metrics
- Business overviews and revenue analysis
- Recent news and market events
- Financial performance summaries
- Risk and opportunity assessments
- Investor sentiment analysis

The application is built using [mcp-agent](https://github.com/lastmile-ai/mcp-agent), a framework for creating AI agents with Model Context Protocol (MCP) integration.

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

Run the finance research agent:

```bash
uv run main.py
```

The application will:
1. Connect to the configured MCP servers
2. Execute the research agent with predefined instructions
3. Generate a comprehensive stock report

### Configuration

The application uses configuration files:
- `mcp_agent.config.yaml` - Main configuration settings
- `mcp_agent.secrets.yaml` - API keys and secrets (not tracked in git)

## Contributing

This project is part of the AI Alliance initiative. We welcome contributions from developers with finance industry expertise, AI expertise, or those looking to grow their skills in either area.

For contribution guidelines, see the [AI Alliance community repo](https://github.com/The-AI-Alliance/community/).

## License

- Code: [Apache 2.0](LICENSE.Apache-2.0)
- Documentation: [Creative Commons Attribution 4.0 International](LICENSE.CC-BY-4.0)
- Data: [Community Data License Agreement - Permissive - Version 2.0](LICENSE.CDLA-2.0)
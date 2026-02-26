# DRA Applications

Deep Research Agent applications for various domains.

This package contains the applications that use the dra-core library:

- **Finance**: Research publicly-traded companies and generate detailed investment research reports.
- **Medical**: Research medical topics and prepare detailed, aggregated reports.

## Installation

First install dra-core:

```bash
# Assuming you are in the dra-apps directory...
cd ../dra-core
pip install -e .
```

Then install the apps:

```bash
cd ../dra-apps
pip install -e .
```

Or with uv:

```bash
cd ../dra-core && uv sync
cd ../dra-apps && uv sync
```

## Usage

See the main project [README](../README.md) for detailed usage instructions.

## License

See the main project [LICENSE](../LICENSE.Apache-2.0) files.
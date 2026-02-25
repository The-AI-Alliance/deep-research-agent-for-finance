# DRA Core

Core library for Deep Research Agent applications.

This package provides the shared functionality used by all DRA applications, including:

- Deep research orchestration
- Observer pattern for monitoring and reporting
- Task management
- Markdown generation utilities
- Rich console display
- Common utilities for paths, prompts, strings, and I/O

## Installation

```bash
pip install dra-core
```

Or with uv:

```bash
uv add dra-core
```

## Development

To install for development:

```bash
cd dra-core
uv sync
```

## Running Tests

```bash
cd dra-core
uv run python -m unittest discover
```

## License

See the main project [LICENSE](../LICENSE.Apache-2.0) files.
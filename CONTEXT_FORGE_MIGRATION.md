# Migration Guide: IBM Context Forge Integration

This guide helps users run the Deep Research Agent for Applications installation with [**IBM Context Forge**](https://ibm.github.io/mcp-context-forge/) for external MCP service invocations, when desired. This is an optional feature.

## Why IBM Context Forge?

[IBM Context Forge](https://ibm.github.io/mcp-context-forge/) is a centralized gateway that provides unified controlled access to approved MCP services. It provides the following benefits:

- **Centralized Authentication**: One token for all external services
- **Usage Monitoring**: Track and analyze MCP service usage
- **Enhanced Security**: Secure proxy layer for external calls
- **Consistent Performance**: Optimized routing and caching
- **Simplified Management**: Single point of configuration

### Services That Would Be Affected

Any of the following services used by this application could route through Context Forge:
- **fetch** - Web content fetching
- **yfmcp** - Yahoo Finance data  
- **financial-datasets** - Financial datasets API

### Services Unchanged

These local services would continue to run without Context Forge:
- **filesystem** - Local file system access
- **excel** - Local Excel file operations

## Migration Steps

This section summarized details also available in the README.

> [!NOTE]
> This description assumes the service base URL is `http://localhost:4444/`, which is the default for local test deployments. Edit the URL as required for your deployment.

### 1. Set Up Context Forge

Follow the [Context Forge documentation](https://ibm.github.io/mcp-context-forge/) instructions to install and run it. For example, see [these instructions](https://ibm.github.io/mcp-context-forge/#1-install-run-copy-paste-friendly).

For queries to the gateway, you need to obtain and configure your Context Forge _bearer token_. Getting the value for this token is also discussed in the [API Endpoints](https://ibm.github.io/mcp-context-forge/#api-endpoints) documentation. Use the environment variable name `MCPGATEWAY_BEARER_TOKEN` for it, e.g.,

```bash
export MCPGATEWAY_BEARER_TOKEN="your-actual-context-forge-token-here"
```

Add this definition to the shell profile (`.bashrc`, `.zshrc`, etc.) for the account that will run the application, in order to make it permanent.

Then see [API Endpoints](https://ibm.github.io/mcp-context-forge/#api-endpoints) for details on adding tools and services with API calls, or use the GUI at the gateway root URL, which is [localhost:4444](https://localhost:4444) when running locally.

### 2. Update the Desired Deep Research Application Configuration File

Edit one or more of the `mcp_agent.config*.yaml` files in the `src/dra/APP/config/` directory corresponding to your application, where `APP` is `finance` or `medical`. Change the `servers` definitions to route external services through Context Forge. Here is how the three external services are currently configured:

```yaml
mcp:
  servers:
    fetch:
      command: "uvx"
      args: ["mcp-server-fetch"]
    yfmcp:
      command: "uvx"
      args: ["yfmcp@latest"]
    financial-datasets:
      command: "npx"
      args: ["-y", "mcp-remote", "https://mcp.financialdatasets.ai/mcp"]
```

If instead you deploy and/or manage access to any of these servers using Context Forge, then change the corresponding definitions as follows, where `<gateway>` is a placeholder for the Context Forge server. For example, if you run a local test instance of Context Forge, `<gateway>` will be `http://localhost:4444` by default.

```yaml
mcp:
  servers:
    # External services routed through IBM Context Forge
    fetch:
      command: "npx"
      args: ["-y", "mcp-remote", "<gateway>/mcp/fetch", 
             "--header", "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}"]
    yfmcp:
      command: "npx"
      args: ["-y", "mcp-remote", "<gateway>/mcp/yfmcp",
             "--header", "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}"]
    financial-datasets:
      command: "npx"
      args: ["-y", "mcp-remote", "<gateway>/mcp/financial-datasets",
             "--header", "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}"]
```

(_MCP Gateway_ was the original name for the IBM Context Forge project.)

This example is also in `examples/mcp_agent.config-context_forge.yaml`.

### 3. Verify Your Setup

Test that the configuration works using a test run one of the deep research applications. Using `make`:

```bash
make APP_ARGS='--short-run' app-run-medical
```

The `--short-run` flag limits iterations for a quick test. (The "research" results will be suboptimal...)


## Troubleshooting

### Authentication Errors

If you see authentication errors:
- Verify your `MCPGATEWAY_BEARER_TOKEN` is set correctly in the environment.
- Check that `mcp_agent.secrets.yaml` exists and contains the token
- Ensure the token hasn't expired

### Service Connection Issues

If services fail to connect:
- Verify you have internet connectivity
- Check that Context Forge is accessible: `curl http://localhost:4444`
- Review logs in the `logs` directory for detailed error messages

### Reverting to Direct Access

If you need to temporarily revert to direct MCP service access (not recommended for production):

1. Edit `mcp_agent.config.yaml` and change the affected services back to their original configuration
2. Remove the Context Forge authentication headers

## Getting Help

- **Context Forge Issues**: Contact your IBM Context Forge administrator.
- **Application Issues**: See the main [README.md](README.md) or open an issue on GitHub
- **Configuration Questions**: Review the [Configuration section](README.md#configuration) in the README

## Additional Resources

- [IBM Context Forge documentation](https://ibm.github.io/mcp-context-forge/) 
- [MCP Agent Configuration Guide](https://docs.mcp-agent.com/reference/configuration)
- [Project README](README.md)

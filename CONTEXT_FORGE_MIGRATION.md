# Migration Guide: IBM Context Forge Integration

This guide helps users run the Deep Research Agent for Applications installation with [**IBM Context Forge**](https://ibm.github.io/mcp-context-forge/) for external MCP service invocations, when desired. This would be useful in enterprise settings with IT wants to carefully manage and monitor MCP server invocations, especially outside the enterprise's firewall.

## Why IBM Context Forge?

[IBM Context Forge](https://ibm.github.io/mcp-context-forge/) is a centralized gateway that provides unified controlled access to approved MCP services. It provides the following benefits:

- **Centralized Authentication**: One token for all external services
- **Usage Monitoring**: Track and analyze MCP service usage
- **Enhanced Security**: Secure proxy layer for external calls
- **Consistent Performance**: Optimized routing and caching
- **Simplified Management**: Single point of configuration

### Refrences

The following documentation will be handy:

* [Context Forge docs](https://ibm.github.io/mcp-context-forge/)
* [`mcp-agent` configuration](https://docs.mcp-agent.com/reference/configuration) - corresponding configuration changes required in `mcp_agent.config*.yaml` files.

### Services That Could Be Served through Context Forge

Most of the services used by the applications could route through Context Forge. We will sketch an example using the medical application's `medical-mcp` MCP server. By default this server is run locally and uses STDIO to communicate with the application agent. The default invocation in the medical  `mcp_agent.config*.yaml` files is `node /path/to/node_modules/medical-mcp/build/index.js`, as discussed in [`apps/medical/README.md`](https://github.com/The-AI-Alliance/deep-research-agent-for-applications/blob/main/src/dra/apps/medical/README.md).

Instead, we will run it on a separate server where Context Forge is running, although actually we will use the same local machine for demonstration purposes. We will then use Context Forge's `mcpgateway.translate` feature to expose this service as both a streamable HTTP and SSE (server-side events) gateway (in Context Forge terminology). This will also expose the ten tools provided by the server. Finally, we will aggregate those tools into a MCP server served by Context Forge. The details are below.

### Services You probably Wouldn't Expose this Way

These local services must continue to run without Context Forge, because they only make sense running locally on your machine:

- **filesystem** - Local file system access
- **excel** - Local Excel file operations (for the finance application)

## Migration Steps

> [!NOTE]
> This description that follows assumes that Context Forge is running locally, where the default base URL will be `http://localhost:4444/`.

### 1. Set Up Context Forge

Follow the [Context Forge documentation](https://ibm.github.io/mcp-context-forge/) instructions to install and run it. Specifically, see [these instructions](https://ibm.github.io/mcp-context-forge/#1-install-run-copy-paste-friendly).

For queries to the gateway, you need to obtain and configure your Context Forge _bearer token_. Getting the value for this token is also discussed in the [API Endpoints](https://ibm.github.io/mcp-context-forge/#api-endpoints) documentation. Use the environment variable name `MCPGATEWAY_BEARER_TOKEN` for it, e.g.,

```bash
export MCPGATEWAY_BEARER_TOKEN="your-actual-context-forge-token-here"
```

Then see [API Endpoints](https://ibm.github.io/mcp-context-forge/#api-endpoints) for details on adding tools and services with API calls, or use the GUI at the gateway root URL, which is [localhost:4444](https://localhost:4444) when running locally.

> [!TIP]
> The Context Forge documentation shows a lot of examples using `curl` and related CLI tools for defining servers, etc. We found it more useful to use these tools than the GUI, most of the time!

### 1. Set Up the MCP Servers

For our example, we used the following CLI commands to explore `medical-mcp` as a streamable HTTP and an SSE service. These commands were adapted from [this documentation page](https://ibm.github.io/mcp-context-forge/#1-install-run-copy-paste-friendly), the _End-to-end demo (register a local MCP server)_ section.

#### 1a. Spin Up the MCP Server

We expose multiple protocols simultaneously. Change `/path/to/...` to match your installation.

```shell
uv run python -m mcpgateway.translate \
  --stdio "node /path/to/node_modules/medical-mcp/build/index.js" \
  --expose-sse \
  --expose-streamable-http \
  --port 9000
```

The server is now accessible via both `/sse` (SSE) and `/mcp` (streamable HTTP) endpoints.

#### 1b. Register The MCP Server with the Gateway

```shell
curl -s -X POST \
  -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"med_mcp","url":"http://localhost:8003/sse"}' \
     http://localhost:4444/gateways
```

#### 1c. Verify the Tool Catalog is Correct and Get the Tool Ids

```shell
curl -s \
  -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  http://localhost:4444/tools | jq 
```

You will see output similar to the following, with lots of the output elided:

```json
[
  {
    "id": "f1a343bfc89f4bfaa285ed07f0162930",
    "originalName": "get-article-details",
    "url": "http://localhost:9000/sse",
    "description": "Get detailed information about a specific medical article by PMID",
    "requestType": "SSE",
    "integrationType": "MCP",
    "headers": null,
    "inputSchema": {
      "type": "object",
      "properties": {
        "pmid": {
          "type": "string",
          "description": "PubMed ID (PMID) of the article"
        }
      },
      "required": [
        "pmid"
      ],
      "additionalProperties": false,
      "$schema": "http://json-schema.org/draft-07/schema#"
    },
    ...
  },
  {
    "id": "3ba475621cff4e66b998f0341a9ad308",
    "originalName": "get-drug-details",
    ...
  },
  ...
]
```

We need the ids. We'll print the names, too, because we only want the `medical-mcp` tools (in case you have others defined, too):

```shell
curl -s \
  -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  http://localhost:4444/tools | jq '.[] | {id, originalName}'
```

```json
{
  "id": "f1a343bfc89f4bfaa285ed07f0162930",
  "originalName": "get-article-details"
}
{
  "id": "3ba475621cff4e66b998f0341a9ad308",
  "originalName": "get-drug-details"
}
{
  "id": "1a34e9d89ce043af939a82c781593f27",
  "originalName": "get-health-statistics"
}
{
  "id": "e706c821dc984e53a7d55df8c1dfdeef",
  "originalName": "search-clinical-guidelines"
}
{
  "id": "c50ed7d582874b3eae6bba20b8fee125",
  "originalName": "search-drug-nomenclature"
}
{
  "id": "2e2143ad0fca4809beecb18552d1661b",
  "originalName": "search-drugs"
}
{
  "id": "2fb17d8c62004c6c9688d52ed49671d6",
  "originalName": "search-google-scholar"
}
{
  "id": "de22fca1716d47a8a4f47709c11cbb63",
  "originalName": "search-medical-databases"
}
{
  "id": "90505ad2cf194378a8872c54b6b5f795",
  "originalName": "search-medical-journals"
}
{
  "id": "40b8137028374b6483ee80184470b99d",
  "originalName": "search-medical-literature"
}
```

Edit those ids into a list of quoted strings, e.g.,

```text
"f1a343bfc89f4bfaa285ed07f0162930","3ba475621cff4e66b998f0341a9ad308","1a34e9d89ce043af939a82c781593f27","e706c821dc984e53a7d55df8c1dfdeef","c50ed7d582874b3eae6bba20b8fee125","2e2143ad0fca4809beecb18552d1661b","2fb17d8c62004c6c9688d52ed49671d6","de22fca1716d47a8a4f47709c11cbb63","90505ad2cf194378a8872c54b6b5f795","40b8137028374b6483ee80184470b99d"
```

#### 1d. Create a Virtual Server Bundling The Tools

Notice where the list of ids is inserted.

```shell
url -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"server":{"name":"med_mcp","description":"Medical MCP Server","associated_tools":["f1a343bfc89f4bfaa285ed07f0162930","3ba475621cff4e66b998f0341a9ad308","1a34e9d89ce043af939a82c781593f27","e706c821dc984e53a7d55df8c1dfdeef","c50ed7d582874b3eae6bba20b8fee125","2e2143ad0fca4809beecb18552d1661b","2fb17d8c62004c6c9688d52ed49671d6","de22fca1716d47a8a4f47709c11cbb63","90505ad2cf194378a8872c54b6b5f795","40b8137028374b6483ee80184470b99d"]}}' \
     http://localhost:4444/servers
```

#### 1e. List the Servers

```shell
curl -s \
  -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  http://localhost:4444/servers | jq
```

```json
[
  {
    "id": "69c220fab3d04fb28f1d0c40d753c45f",
    "name": "med_mcp",
    "description": "Medical MCP Server",
    "icon": null,
    "createdAt": "2026-02-24T19:18:18.946501",
    "updatedAt": "2026-02-24T19:18:18.946503",
    "enabled": true,
    "associatedTools": [
      "med-mcp-get-health-statistics",
      "med-mcp-search-drugs",
      "med-mcp-search-google-scholar",
      "med-mcp-get-drug-details",
      "med-mcp-search-medical-literature",
      "med-mcp-search-medical-journals",
      "med-mcp-search-drug-nomenclature",
      "med-mcp-search-medical-databases",
      "med-mcp-search-clinical-guidelines",
      "med-mcp-get-article-details"
    ],
    "associatedResources": [],
    "associatedPrompts": [],
    "associatedA2aAgents": [],
    "metrics": {
      "totalExecutions": 0,
      "successfulExecutions": 0,
      "failedExecutions": 0,
      "failureRate": 0.0,
      "minResponseTime": null,
      "maxResponseTime": null,
      "avgResponseTime": null,
      "lastExecutionTime": null
    },
    "tags": [],
    "createdBy": "...",
    "createdFromIp": "127.0.0.1",
    "createdVia": "api",
    "createdUserAgent": "curl/8.7.1",
    "modifiedBy": null,
    "modifiedFromIp": null,
    "modifiedVia": null,
    "modifiedUserAgent": null,
    "importBatchId": null,
    "federationSource": null,
    "version": 1,
    "teamId": "bec0ce23338549529227c74b071f4a31",
    "team": "Platform Administrator's Team",
    "ownerEmail": "...",
    "visibility": "public"
  }
]

```

You can also connect to the SSE endpoint, which prints a few lines and then waits indefinitely:

```shell
$ curl -s \
  -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
  http://localhost:4444/servers/69c220fab3d04fb28f1d0c40d753c45f/sse

event: endpoint
data: http://localhost:4444/servers/69c220fab3d04fb28f1d0c40d753c45f/message?session_id=0e28b291-eec8-40e4-b9df-93d8d7cfd372
retry: 5000

event: keepalive
data: {}
retry: 5000

^C
```

Note the `69c220fab3d04fb28f1d0c40d753c45f`, which is the server's id that was returned in the previous JSON output.

#### 1f. Client HTTP endpoint - use MCP Inspector?

The MCP inspector is a useful tool for examining a service. The Context Forge instructions suggest using it as follows to inspect the service, _but this did not work for us!_ We'll discuss the details in a moment, but for completeness, here are the instructions:

```shell
npx -y @modelcontextprotocol/inspector
```

Then in the GUI, select for **Transport Type** _Streamable HTTP_, and for the URL: `http://localhost:4444/servers/UUID_OF_SERVER/mcp`, where `UUID_OF_SERVER` is replaced by the id shown in the previous step, which is `69c220fab3d04fb28f1d0c40d753c45f` for us.

However, we said this doesn't work. A _connection error_ is reported, which appears to caused by the expectation by the inspector that the HTTP `OPTION` command can be used (which is supposed to return the supported methods, e.g., `GET`, `POST`, etc.)

How can you tell? Several ways.

If you look at the Context Forge log output (which probably have streaming in a terminal window right now), you will see messages like this:

```
2026-02-25 13:07:13,487 - mcpgateway.services.structured_logger - INFO - [http_gateway] Request started: OPTIONS /servers/69c220fab3d04fb28f1d0c40d753c45f/sse
2026-02-25 13:07:13,491 - mcpgateway.services.structured_logger - WARNING - [http_gateway] Request completed: OPTIONS /servers/69c220fab3d04fb28f1d0c40d753c45f/sse - 405
```

Note the `405` HTTP code, which is `Method Not Allowed`. You should see similar messages in the log output from the running `mcpgateway.translate` command we used above to start the server:

```shell
INFO:     127.0.0.1:61130 - "OPTIONS /sse HTTP/1.1" 405 Method Not Allowed
```

Finally, you can try this `curl`:

```shell
$ curl -s -X OPTIONS \
    -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
    http://localhost:4444/servers/69c220fab3d04fb28f1d0c40d753c45f/sse
{"detail":"Method Not Allowed"}
```

This appears to be default behavior for the `mcpgateway.translate` feature. We tried it with other popular MCP servers and saw the same behavior.

Incidentally, you can use `@modelcontextprotocol/inspector` directly with the `medical-mcp` server. After starting the inspector, select _STDIO_ for the **Transport Type**, then enter `node` for the **Command** and `/path/to/node_modules/medical-mcp/build/index.js` (changing `/path/to` of course) for the **Arguments**. (This will start a new server, if you already have it running.)
The same approach works for other STDIO MCP servers, too.

### 2. Update the Desired Deep Research Application Configuration File

With the MCP server provided by Context Forge, we now change the `mcp_agent.config*.yaml` files in the `src/dra/medical/config/` directory. Here is how the `medical-mcp` server is currently configured to run locally. The other two services, `fetch` and `filesystem` are elided:

```yaml
mcp:
  servers:
    ...
    medical-mcp:
      command: "node"
      "args": ["/path/to/lib/node_modules/medical-mcp/build/index.js"]
    ...
```

Replace this definition with the following:

```yaml
mcp:
  servers:
    ...
    medical-mcp:
      transport: streamable_http
      url: "http://localhost:4444/servers/69c220fab3d04fb28f1d0c40d753c45f/mcp"
      headers:
        Authorization: "Bearer ${MCPGATEWAY_BEARER_TOKEN}"
      http_timeout_seconds: 30
      read_timeout_seconds: 120
    ...
```

The `*_timeout_seconds` values could be adjusted as you see fit. consider longer values if log entries indicate premature connection closures.

Alternatively, the SEE endpoint could be used:

```yaml
mcp:
  servers:
    ...
    medical-mcp:
      transport: sse
      url: "http://localhost:4444/servers/69c220fab3d04fb28f1d0c40d753c45f/sse"
      auth:
        api_key: "${MCPGATEWAY_BEARER_TOKEN}"
    ...
```

This alternative would also avoid HTTP connection timeouts, if those become an issue.

## Troubleshooting

### Authentication Errors

If you see authentication errors:
- Verify your `MCPGATEWAY_BEARER_TOKEN` is set correctly in the environment or check that the `mcp_agent.secrets.yaml` exists and contains the token.
- Ensure the token hasn't expired. For example, a new one will be required when you restart Context Forge.

### Service Connection Issues

If services fail to connect:
- Verify you have internet connectivity.
- Check that Context Forge is accessible: `curl http://localhost:4444`.
- Review `mcp-agent` logs in the `logs` directory for detailed error messages.
- Review the stdout and logs from the services running, including for Context Forge and the `mcpgateway.translate` server process.

## Getting Help

- See the Context Forge/MCP Gateway repo [discussion](https://github.com/IBM/mcp-context-forge/discussions) and [issues](https://github.com/IBM/mcp-context-forge/issues).

## Additional Resources

- Context Forge 
  - [documentation](https://ibm.github.io/mcp-context-forge/) 
  - [repo](https://github.com/IBM/mcp-context-forge)
- [MCP Agent Configuration Guide](https://docs.mcp-agent.com/reference/configuration)

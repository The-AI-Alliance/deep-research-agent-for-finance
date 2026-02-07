# README for `src/dra/apps/*/config`

By default, `mcp_agent.config.yaml` will be used, if you specify either provider `openai` (the default) or `anthropic`.

If you specify `ollama`, the app uses `mcp_agent.config.ollama.yaml` instead.

This is because the inference code path in the `mcp-agent` library uses the OpenAI API for both OpenAI and Ollama inference, but the settings have to be different. This is something of hack to make all three both alternatives transparent. Suggestions for a better solution are welcome!

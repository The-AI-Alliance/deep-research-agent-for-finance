# Meeting Notes

## July 14, 2025

Attendees: Andrew, Phil, Dave, Adam

### Idea: Do a Deep Research Agent for finance

Important requirement: Need to integrate different brokers of data. Could IBM help broker integration to some proprietary data providers? Which ones if any are accessible through MCP. 

We should also acquire some representative sample data, especially for the "download and try" users.

### Details Brainstorming

* `uv`, `.gitignore`, etc.
* Probably need about ~2-5K lines of code. Not a huge code base typically for research agents.
* Do a few "tracer bullet" use cases, deep and detailed, but not so broad that it makes the project unwieldy as a learning/example tool. Some possibilities:
  * Integrate with tools like Excel.
    * Supported in MCP?? (https://www.reddit.com/r/mcp/comments/1jrxcdr/is_there_a_good_excel_mcp_server/)
    * Prior experience with integrations into MS Office were difficult.
    * Could start with an export function to export data that can be imported into Excel.
  * Other use cases TBD.
* Model inference?
  * Should be configable, but what's the best or most likely options.
    * Their open source framework has an abstraction.
  * Open source vs. commercial service options should be considered.
  * We could write an evaluation of different options as part of our deliverables.
    * Azure OpenAI inference most common service in use.
    * Companies have the usual concerns about data privacy and protection.
    * They have liability concerns, too. (More common with Banks and high visibility initiatives)
    * Anthropic Claude is not very popular, except with developers for their tasks.
    * The choice is heavily driven by purchasing processes, e.g., companies that are already big MS customers are more likely to use Azure Open AI services. Google is getting some big wins, too.

### Timeline Goals

* Have something solid in a month.
  
### Action Items
- [ ] Create [issues](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues) for ideas of things to do, flesh-out ideas. ([Project Dashboard](https://github.com/orgs/The-AI-Alliance/projects/42)). [Discussions](https://github.com/The-AI-Alliance/ai-in-finance-example-app/discussions) can be used, too.
- [ ] Reach out to other Alliance members in Finance to get them involved. (Dean)

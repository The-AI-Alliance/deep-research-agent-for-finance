# Meeting Notes


## July 21, 2025

* **Attendees:** Andrew Hoh, Dave Nielsen, Adam Pingel, Dean Wampler 
* **Gemini Notes:** [link](https://docs.google.com/document/d/1Y9BWRFbMmXiTZteBw6FWb1F_4GOpI__agse-2cGwkfc/edit?usp=sharing)

### What Features/Tasks Should We Do Next?

* Blog post - when the project is "meaty enough" to talk about.
* What best techniques can be discussed in meetups, conferences, etc.
* Move to a deep research architecture <-- What LastMile wants to showcase the most
  * Phil used to be an investment banker; knows the space, so he's a good source of requirements, use cases...
  * Aggregating into Excel key data from third-party data sources used in market research is a big time saver.
* We need to find and aggregate more data sources, accessed using MCP
* Next few weeks?
  * Find a good Excel MCP server
    * V1 use case: user enters a symbol, app returns data into a table.
      * Graphs not required
      * Validation of returned results not required; difficult, a possible "V2" feature.
  * Find some useful data sources
  * Break out the current app into more components towards the desired architecture, e.g., separate smaller services and an "aggregator".

### Action Items
- [ ] Dean: Create issues for the next few week's tasks.

## July 14, 2025

* **Attendees:** Andrew Hoh, Phil Chang, Dave Nielsen, Adam Pingel, Dean Wampler 
* **Gemini Notes:** [link](https://docs.google.com/document/d/1gFvfIxcRBaPRMHC3y82JvaLO5glihtpGDhLmFwTHoQM/edit?usp=sharing)

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

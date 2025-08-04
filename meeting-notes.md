# Meeting Notes

* [Issues](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues)
* [Project Dashboard](https://github.com/orgs/The-AI-Alliance/projects/42)

## August 4, 2025

* **Attendees:** Andrew Hoh, Phil Chang, Dean Wampler, Elad Levi (PlurAI), Dave Nielsen 
* **Gemini Notes:** [link](https://docs.google.com/document/d/1xA722_Sv-K5NKvUWFNGqESbrLUOM21bm40Rh4LQNASk/edit?usp=sharing)

### Topics

* Next steps for the excel server?
    * Close _Find a good OSS Excel MCP integration_ [#3](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues/3)?
    * E.g., _User queries for data about an organization from Excel and the results are returned into the spreadsheet_ [#5](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues/5)?
* Progress on datasets? [#4](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues/4).
* Status of `mcp-agent` [PR #346](https://github.com/lastmile-ai/mcp-agent/pull/346):  _Implement AdaptiveWorkflow, a dynamic orchestrator agent_.
    * Blocker for _Begin refactoring towards the desired app architecture_ [#7](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues/7)?
* Testing?

### Action Items
- [ ] ?

## July 28, 2025

* **Attendees:** Andrew Hoh, Phil Chang, Dean Wampler, Elad Levi (PlurAI), Dave Nielsen 
* **Gemini Notes:** [link](https://docs.google.com/document/d/1xA722_Sv-K5NKvUWFNGqESbrLUOM21bm40Rh4LQNASk/edit?usp=sharing)

### From Last Week
* Find a good Excel server.
  * Most popular one?? https://github.com/haris-musa/excel-mcp-server.
    * Needs to be validated. (A good thing to document? How to do this for any server??)
    * Hopefully MS will release one of their own.
* Find useful data sources.
  * Andrew looked at some. Good ones tend to charge for use. Less popular ones will need a lot more testing.
  * E.g., 10Ks, financial reports (official ones better), latest relevant news, aggregators.
  * See the [SEC EDGAR search](https://www.sec.gov/edgar/search/).
    * From it you can extract very interesting finance information on all US public companies.
    * [FinanceBench](https://arxiv.org/abs/2311.11944) was built with this data.
  * A synthetic dataset for a fictitious company, etc.
    * But people will care about accuracy, so how would this work?
* Evolve towards the desired architecture...
  * Dean started a PR to move the current `main.py` file to `src/finance-deep-search` (name TBD...) and create a corresponding test directory.
  * See: https://github.com/lastmile-ai/mcp-agent/tree/feature/adaptive_workflow/src/mcp_agent/workflows/adaptive
    * Branch will be merged soon.
    * Similar to the model described by Anthropic's [blog post](https://www.anthropic.com/engineering/built-multi-agent-research-system) on deep research.
    * What "evangelism" should we do right now? (See also the [blog post ticket](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues/6).)

### Action Items
- [ ] Dave: Reach out to community people for help validating 3rd-party servers.
- [ ] Keep looking for data sources, e.g., from other AIA members? (Dean and Dave: look at the membership...)
- [x] Dean: Update issues with relevant notes here.
- [ ] Dave: Follow up on "evangelism" opportunities.
- [x] Dean: Next steps for PR process improvements.


## July 21, 2025

* **Attendees:** Andrew Hoh, Sarmad Qadri, Dave Nielsen, Adam Pingel, Dean Wampler 
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
- [x] Dean: Create issues for the next few week's tasks.

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
- [x] Create [issues](https://github.com/The-AI-Alliance/ai-in-finance-example-app/issues) for ideas of things to do, flesh-out ideas. ([Project Dashboard](https://github.com/orgs/The-AI-Alliance/projects/42)). [Discussions](https://github.com/The-AI-Alliance/ai-in-finance-example-app/discussions) can be used, too.
- [x] Reach out to other Alliance members in Finance to get them involved. (Dean)

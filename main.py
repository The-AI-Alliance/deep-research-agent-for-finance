import asyncio
import os
import time

from mcp_agent.app import MCPApp
from mcp_agent.config import (
    Settings,
    LoggerSettings,
    MCPSettings,
    MCPServerSettings,
    OpenAISettings,
    AnthropicSettings,
)
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.llm_selector import ModelPreferences
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import (
    EvaluatorOptimizerLLM,
    QualityRating,
)

app = MCPApp(name="finance_deep_research")  # settings=settings)


async def example_usage():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

        research_agent = Agent(
            name="research_agent",
            instruction="""
            You are a top-tier financial research analyst. Your task is to gather a comprehensive and up-to-date profile on the following publicly traded company: {stock_ticker}. 

            Perform research across reliable financial news sites, stock analysis platforms, and official company sources. Use the following websites as a starting point for data collection:

            - https://finance.yahoo.com/quote/{stock_ticker}/financials/
            - https://www.cnbc.com/quotes/{stock_ticker}?tab=financials
            - https://www.marketwatch.com/investing/stock/{stock_ticker}/financials?mod=mw_quote_tab

            Your goal is to synthesize key insights in a structured and investor-relevant way.

            Required Output Structure:

            1. Basic Stock Information
            - Ticker Symbol:
            - Exchange:
            - Sector / Industry:
            - Market Cap:
            - Current Price (with date/time):
            - 52-Week High/Low:

            2. Financial Performance
            - Summary of last 2 earnings reports (EPS, Revenue, YoY growth):
            - Analyst consensus (Buy/Hold/Sell) with brief explanation:

            3. Optional Add-ons (if available)
            - Charts or metrics (P/E ratio, PEG, Dividend Yield, Beta):
            - Forecasts (price targets, growth estimates):

            Research Instructions:
            - Prioritize accuracy, recency, and source credibility.
            - Prefer structured data (e.g., from Yahoo Finance, Bloomberg, Reuters, SEC filings).
            - When summarizing opinions (e.g., analyst consensus), clearly distinguish fact vs. interpretation.
            """,
            server_names=["fetch"],
        )

                # Quality control agent that enforces strict data standards
        research_evaluator = Agent(
            name="data_evaluator",
            instruction=f"""You are a strict financial data quality evaluator for company research.
            
            **EVALUATION CRITERIA:**
            
            1. **COMPLETENESS CHECK** (Must have ALL of these):
               ✓ Current stock price with exact dollar amount and percentage change
               ✓ Latest quarterly EPS with actual vs estimate comparison
               ✓ Latest quarterly revenue with actual vs estimate comparison  
               ✓ At least 3 recent financial news items with dates and sources
               ✓ Key financial metrics (P/E ratio, market cap)
               ✓ All data has proper source citations with URLs
            
            2. **ACCURACY CHECK**:
               ✓ Numbers are specific (not "around" or "approximately")
               ✓ Dates are recent and clearly stated
               ✓ Sources are credible financial websites
               ✓ No conflicting information without explanation
            
            3. **CURRENCY CHECK**:
               ✓ Stock price data is from today or latest trading day
               ✓ Earnings data is from most recent quarter
               ✓ News items are from last 7 days (or most recent available)
            
            **RATING GUIDELINES:**
            
            - **EXCELLENT**: All criteria met perfectly, comprehensive data, multiple source verification
            - **GOOD**: All required data present, good quality sources, minor gaps acceptable
            - **FAIR**: Most required data present but missing some elements or has quality issues
            - **POOR**: Missing critical data (stock price, earnings, or major sources), unreliable sources
            
            **IMPROVEMENT FEEDBACK:**
            [Specific instructions for what needs to be improved, added, or fixed]
            [If rating is below GOOD, provide exact search queries needed]
            [List any missing data points that must be found]
            
            **CRITICAL RULE**: If ANY of these are missing, overall rating cannot exceed FAIR:
            - Exact current stock price with change
            - Latest quarterly EPS actual vs estimate  
            - Latest quarterly revenue actual vs estimate
            """,
            server_names=[],
        )

        # Create the research quality control component
        research_quality_controller = EvaluatorOptimizerLLM(
            optimizer=research_agent,
            evaluator=research_evaluator,
            llm_factory=OpenAIAugmentedLLM,
            min_rating=QualityRating.GOOD,
        )

        # Quality control agent that enforces strict data standards
        excel_agent = Agent(
            name="excel_evaluator",
            instruction="""You are a top-tier financial research analyst. Your task is to generate a excel sheet with financials for the following publicly traded company: {stock_ticker}. 

            Create a new excel document following the naming convention: `/tmp/financials_{stock_ticker}.xlsx` within the current directory. Use the context about the financials provided to populate the excel sheet.

            Example of a markdown table for financials would look like this:
            | **Account**                         | **FY 2022** | **FY 2023** | **FY 2024** | **FY 2025E** |
            |-------------------------------------|-----------:|-----------:|-----------:|------------:|
            | **Revenue**                         |            |            |            |             |
            | • Net Sales                         |    100,000 |    120,000 |    140,000 |     160,000 |
            | • Other Revenue                     |      5,000 |      6,000 |      7,000 |       8,000 |
            | **Cost of Goods Sold**              |            |            |            |             |
            | • Materials & Production Costs      |   (60,000) |   (72,000) |   (84,000) |    (96,000) |
            | • Freight & Handling                |    (2,000) |    (2,400) |    (2,800) |     (3,200) |
            | **Gross Profit**                    |    43,000  |    51,600  |    60,200  |     68,800  |
            | **Gross Margin**                    |     38.6%  |     38.9%  |     39.0%  |      39.4%  |
            |                                     |            |            |            |             |
            | **Operating Expenses**              |            |            |            |             |
            | • R&D                               |   (10,000) |   (11,000) |   (12,000) |    (13,000) |
            | • SG&A                              |   (15,000) |   (16,500) |   (18,000) |    (19,500) |
            | **Total Operating Expenses**        |   (25,000) |   (27,500) |   (30,000) |    (32,500) |
            | **Operating Income**                |    18,000  |    24,100  |    30,200  |     36,300  |
            | **Operating Margin**                |     17.1%  |     18.3%  |     18.6%  |      19.3%  |
            |                                     |            |            |            |             |
            | **Non-Operating**                   |            |            |            |             |
            | • Interest Expense                  |    (1,000) |    (1,100) |    (1,200) |     (1,300) |
            | • Other Income (Expense)            |       500  |       600  |       700  |       800   |
            | **Pre-Tax Income**                  |    17,500  |    23,600  |    29,700  |     35,800  |
            | • Income Tax Expense (25%)          |    (4,375) |    (5,900) |    (7,425) |     (8,950) |
            | **Net Income**                      |    13,125  |    17,700  |    22,275  |     26,850  |
            | **Net Margin**                      |     12.0%  |     12.8%  |     13.2%  |      13.4%  |
            """,
            server_names=["excel"],
        )

        result = await research_quality_controller.generate_str(
            message=f"Research for me the quarterly earnings of Meta Platforms",
            request_params=RequestParams(model="gpt-4o"),
        )

        llm = await excel_agent.attach_llm(OpenAIAugmentedLLM)
        result = await llm.generate_str(
            message="Context on found research: " + result,
        )


if __name__ == "__main__":
    start = time.time()
    asyncio.run(example_usage())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")
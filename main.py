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

app = MCPApp(name="finance_deep_research")  # settings=settings)


async def example_usage():
    async with app.run() as agent_app:
        logger = agent_app.logger
        context = agent_app.context

        logger.info("Current config:", data=context.config.model_dump())

        research_agent = Agent(
            name="research_agent",
            instruction="""
            You are a top-tier financial research analyst. Your task is to gather a comprehensive and up-to-date profile on the following publicly traded company: {stock_ticker}. Then output a structured report in the output directory.

            Perform research across reliable financial news sites, stock analysis platforms, and official company sources. Use the following websites as a starting point for data collection:

            - https://finance.yahoo.com/quote/{stock_ticker}
            - https://www.cnbc.com/quotes/{stock_ticker}
            - https://www.marketwatch.com/investing/stock/{stock_ticker}

            Your goal is to synthesize key insights in a structured and investor-relevant way.

            Required Output Structure:

            1. Basic Stock Information
            - Ticker Symbol:
            - Exchange:
            - Sector / Industry:
            - Market Cap:
            - Current Price (with date/time):
            - 52-Week High/Low:

            2. Business Overview
            - One-paragraph company summary:
            - Key products or services:
            - Primary sources of revenue:

            3. Recent News and Events
            - Top 3–5 recent headlines (with links and dates):
            - Notable earnings, mergers, or partnerships:

            4. Financial Performance
            - Summary of last 2 earnings reports (EPS, Revenue, YoY growth):
            - Analyst consensus (Buy/Hold/Sell) with brief explanation:

            5. Key Risks and Opportunities
            - Major risks (regulatory, macroeconomic, etc.):
            - Growth opportunities or strategic advantages:

            6. Investor Sentiment
            - Notable institutional investors or changes in ownership:
            - Social media/retail sentiment (Reddit, X, Stocktwits if relevant):

            7. Optional Add-ons (if available)
            - Charts or metrics (P/E ratio, PEG, Dividend Yield, Beta):
            - Forecasts (price targets, growth estimates):

            Research Instructions:
            - Prioritize accuracy, recency, and source credibility.
            - Prefer structured data (e.g., from Yahoo Finance, Bloomberg, Reuters, SEC filings).
            - When summarizing opinions (e.g., analyst consensus), clearly distinguish fact vs. interpretation.
            """,
            server_names=["fetch"],
        )

        async with research_agent:
            logger.info("finder: Connected to server, calling list_tools...")
            result = await research_agent.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            llm = await research_agent.attach_llm(OpenAIAugmentedLLM)

            result = await llm.generate_str(
                message="Research for me the quarterly earnings of Meta Platforms",
            )
            logger.info(f"Research Summary: {result}")

if __name__ == "__main__":
    start = time.time()
    asyncio.run(example_usage())
    end = time.time()
    t = end - start

    print(f"Total run time: {t:.2f}s")
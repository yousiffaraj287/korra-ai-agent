"""
File: graph.py
Project: Korra AI Agent
Author: Yousif Faraj

Description:
    Core orchestration graph for the Korra AI agent system using LangGraph.
    This module defines the conversation state, tool routing, and node
    execution flow for a tool-augmented assistant.

    Key capabilities:
      • Web search via Tavily
      • Local file analysis via a C-based file_stats tool (invoked with subprocess)
      • GitHub operations via an MCP server (Model Context Protocol)

    Notes:
      • Secrets/keys should be provided via environment variables (do not commit .env):
        OPENAI_API_KEY, TAVILY_API_KEY, GITHUB_TOKEN (or equivalent).
"""

from __future__ import annotations

import os
import json
import logging
import asyncio
import subprocess
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearch

# MCP (GitHub) integration
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

# -------------------------------------------------------------
# Logging
# -------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# -------------------------------------------------------------
# Constants / defaults
# -------------------------------------------------------------
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_SEARCH_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "3"))

# -------------------------------------------------------------
# Graph State
# -------------------------------------------------------------
class State(TypedDict):
    """
    State schema for the Korra graph used by LangGraph Studio.

    LangGraph Studio's message composer automatically manages this state,
    adding new messages and preserving full conversation history across
    interactions. The add_messages merge policy ensures that messages are
    appended rather than replaced.

    Fields:
        messages: Full conversation history (Human and AI messages).
                  Studio displays this in the state inspector, allowing
                  developers to see how context is maintained across turns.
    """
    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================
# MCP SERVER INITIALIZATION
# ============================================================

async def build_mcp_tools() -> list:
    """
    Build tools dynamically from an MCP server configuration.

    This loads tool definitions at runtime so the agent can call external
    capabilities (e.g., GitHub operations) without hard-coding each tool.
    """
    github_token = os.getenv("GITHUB_TOKEN")

    # MCP server config (GitHub)
    # Note: keep tokens in env vars; do not commit them to the repo.
    mcp_config = {
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_TOKEN": github_token} if github_token else {},
        }
    }

    client = MultiServerMCPClient(mcp_config)

    # Load MCP tool wrappers
    tools = await load_mcp_tools(client)
    return tools


# ============================================================
# TOOL NODES
# ============================================================

def initialize_korra() -> StateGraph:
    """
    Build and return a compiled LangGraph StateGraph for the Korra AI agent.

    Nodes:
      - agent: Primary LLM node with tool calling enabled.
      - tavily_tool: Web search tool node (sync).
      - file_stats_tool: Local C-based file statistics tool node (subprocess).
      - github_mcp_tool: Async node to execute MCP tools (GitHub).

    Returns:
        A compiled graph ready for Studio / local execution.
    """
    # Initialize the language model
    llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0.7)

    # Initialize the web search tool for real-time information retrieval
    tavily_tool = TavilySearch(max_results=MAX_SEARCH_RESULTS)

    # Initialize the local C-based file statistics tool
    # Expected executable: ./file_stats (or adjust as needed)
    file_stats_exe = os.getenv("FILE_STATS_EXE", "./file_stats")

    # ---------------------------------------------------------
    # Tool node: Tavily
    # ---------------------------------------------------------
    def tavily__tool(state: State) -> dict[str, list[BaseMessage]]:
        """
        Execute web search tool calls.

        This node runs synchronous tool calls that do not require async handling.
        """
        result = tavily_tool.invoke(state["messages"][-1].content)
        return {"messages": [result]}

    # ---------------------------------------------------------
    # Tool node: File stats (C program)
    # ---------------------------------------------------------
    def file_stats__tool(state: State) -> dict[str, list[BaseMessage]]:
        """
        Execute C-based file statistics tool calls.

        This node invokes a compiled C program via subprocess, demonstrating
        cross-language integration. Keeping file analysis behind a dedicated
        node makes it easy to debug subprocess execution and output parsing.
        """
        prompt = state["messages"][-1].content

        try:
            # Invoke the C tool. Adjust CLI args to match your C program contract.
            proc = subprocess.run(
                [file_stats_exe, prompt],
                capture_output=True,
                text=True,
                check=False,
            )

            if proc.returncode != 0:
                msg = f"file_stats tool error (rc={proc.returncode}): {proc.stderr.strip()}"
                log.warning(msg)
                return {"messages": [msg]}

            out = proc.stdout.strip()

            # If the tool returns JSON, keep it as JSON; otherwise pass raw.
            try:
                parsed = json.loads(out)
                return {"messages": [json.dumps(parsed, indent=2)]}
            except Exception:
                return {"messages": [out]}

        except FileNotFoundError:
            msg = f"file_stats executable not found: {file_stats_exe}"
            log.error(msg)
            return {"messages": [msg]}
        except Exception as e:
            msg = f"file_stats tool exception: {type(e).__name__}: {e}"
            log.exception(msg)
            return {"messages": [msg]}

    # ---------------------------------------------------------
    # Tool node: GitHub MCP (async)
    # ---------------------------------------------------------
    async def github_mcp__tool(state: State) -> dict[str, list[BaseMessage]]:
        """
        Execute MCP tool calls asynchronously (e.g., GitHub operations).

        This node is async because MCP calls may involve network I/O and
        dynamic tool selection at runtime.
        """
        mcp_tools = await build_mcp_tools()

        # Bind MCP tools to the model for tool calling behavior.
        # (Depending on your LangChain version, binding may vary.)
        mcp_llm = llm.bind_tools(mcp_tools)

        response = await mcp_llm.ainvoke(state["messages"])
        return {"messages": [response]}

    # ---------------------------------------------------------
    # Agent node
    # ---------------------------------------------------------
    def agent(state: State) -> dict[str, list[BaseMessage]]:
        """
        Main LLM node.

        The model is bound to the locally available tools. Tool routing is
        handled by the graph's conditional edges based on the requested action.
        """
        # Combine all available tools for LLM binding (sync tools only here)
        tools_for_binding = [tavily_tool]
        agent_llm = llm.bind_tools(tools_for_binding)

        response = agent_llm.invoke(state["messages"])
        return {"messages": [response]}

    # ============================================================
    # GRAPH BUILDING
    # ============================================================
    graph_builder = StateGraph(State)

    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tavily_tool", tavily__tool)
    graph_builder.add_node("file_stats_tool", file_stats__tool)

    # Async node wrapper for MCP:
    # LangGraph supports async nodes; we expose it as a node name here.
    graph_builder.add_node("github_mcp_tool", github_mcp__tool)

    # ---------------------------------------------------------
    # Routing logic
    # ---------------------------------------------------------
    def route_tools(state: State) -> str:
        """
        Decide which node to route to based on the latest message.

        You can make this smarter by inspecting tool_calls metadata.
        This is intentionally simple and readable.
        """
        last = state["messages"][-1]

        # If LangChain tool calling is used, tool calls may be available here.
        tool_calls = getattr(last, "tool_calls", None) or []

        if tool_calls:
            # Route based on tool name
            name = tool_calls[0].get("name", "").lower()
            if "tavily" in name:
                return "tavily_tool"
            if "file" in name or "stats" in name:
                return "file_stats_tool"
            if "github" in name:
                return "github_mcp_tool"

        # Fallback routing: keep conversation in the agent loop
        return END

    # Agent decides, then we route to a tool node (or end)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges("agent", route_tools)

    # Tool nodes return control to the agent for the next step
    graph_builder.add_edge("tavily_tool", "agent")
    graph_builder.add_edge("file_stats_tool", "agent")
    graph_builder.add_edge("github_mcp_tool", "agent")

    # Compile and return the graph
    return graph_builder.compile()


# Create the graph instance that Studio will discover and load
graph = initialize_korra()

# Status visibility logs (useful when running under LangGraph Studio or Docker)
log.info("Korra graph initialized successfully with GitHub MCP integration")
log.info("Available tools: Tavily (web search), file_stats (C program), GitHub MCP")

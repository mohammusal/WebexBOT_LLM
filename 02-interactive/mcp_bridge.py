"""
MCP Bridge — Generic connector between any stdio MCP server and OpenAI.

This module spawns an MCP server as a subprocess, keeps a persistent session
alive on a background async thread, and exposes synchronous methods that any
bot framework can call:

    bridge = MCPBridge(server_command, server_args, server_cwd)
    bridge.start()                       # spawns server, discovers tools
    result = bridge.run(messages)        # agentic tool-calling loop → final text
    bridge.shutdown()                    # clean teardown

The bridge is SERVER-AGNOSTIC — it works with any MCP server over stdio.
Point MCP_SERVER_COMMAND / MCP_SERVER_ARGS / MCP_SERVER_CWD at any server.
"""

import asyncio
import json
import logging
import threading
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

log = logging.getLogger(__name__)

MAX_LOOP_ITERATIONS = 10
CALL_TIMEOUT_SECONDS = 60


class MCPBridge:
    """Bridges a stdio MCP server to OpenAI function-calling."""

    def __init__(
        self,
        server_command: str,
        server_args: list[str] | None = None,
        server_cwd: str | None = None,
        server_env: dict[str, str] | None = None,
        model: str = "gpt-4o-mini",
        max_iterations: int = MAX_LOOP_ITERATIONS,
    ):
        self._server_params = StdioServerParameters(
            command=server_command,
            args=server_args or [],
            cwd=server_cwd,
            env=server_env,
        )
        self._model = model
        self._max_iterations = max_iterations

        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._session: ClientSession | None = None
        self._openai_tools: list[dict[str, Any]] = []
        self._ready = threading.Event()
        self._startup_error: Exception | None = None
        self._openai = OpenAI()
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Spawn the MCP server and establish a session (blocking)."""
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=30):
            raise RuntimeError("MCPBridge failed to start within 30 seconds")
        if self._session is None:
            raise RuntimeError(
                f"MCPBridge: server failed to connect — {self._startup_error}"
            )
        log.info("MCPBridge ready — %d tools discovered", len(self._openai_tools))

    def shutdown(self) -> None:
        """Shut down the MCP session and stop the event loop."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=10)
        log.info("MCPBridge shut down")

    def _run_loop(self) -> None:
        """Background thread: run the async event loop that owns the MCP session."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._session_lifecycle())

    async def _session_lifecycle(self) -> None:
        """Connect to MCP server, discover tools, then keep the loop alive."""
        try:
            async with stdio_client(self._server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    self._session = session

                    tools_result = await session.list_tools()
                    self._openai_tools = self._translate_tools(tools_result.tools)

                    self._ready.set()
                    # Keep the loop alive until stopped
                    while True:
                        await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            import sys
            print(f"\n❌ MCP BRIDGE ERROR: {exc}\n", file=sys.stderr)
            log.error("MCP session error: %s", exc)
            self._startup_error = exc
            self._ready.set()

    # ------------------------------------------------------------------
    # Tool Discovery & Schema Translation
    # ------------------------------------------------------------------

    def _translate_tools(self, mcp_tools: list) -> list[dict[str, Any]]:
        """Convert MCP tool schemas to OpenAI function-calling specs."""
        openai_tools = []
        for tool in mcp_tools:
            spec = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema if tool.inputSchema else {"type": "object", "properties": {}},
                },
            }
            openai_tools.append(spec)
        return openai_tools

    def get_openai_tools(self) -> list[dict[str, Any]]:
        """Return cached OpenAI tool specs (call after start())."""
        return self._openai_tools

    # ------------------------------------------------------------------
    # Agentic Tool-Calling Loop
    # ------------------------------------------------------------------

    def run(self, messages: list[dict[str, Any]], timeout: float = CALL_TIMEOUT_SECONDS) -> str:
        """Synchronous entry point: run the agentic loop and return final text."""
        if not self._loop or not self._session:
            return "⚠️ MCP Bridge is not connected. Please try again later."
        future = asyncio.run_coroutine_threadsafe(
            self._agentic_loop(messages), self._loop
        )
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            return "⚠️ Request timed out. The MCP server may be slow or unresponsive."
        except Exception as exc:
            log.exception("Agentic loop error")
            return f"⚠️ Error: {exc}"

    async def _agentic_loop(self, messages: list[dict[str, Any]]) -> str:
        """Run the tool-calling loop until the LLM produces a text-only response."""
        async with self._lock:
            tools = self._openai_tools
            working_messages = list(messages)

            for iteration in range(self._max_iterations):
                response = self._openai.chat.completions.create(
                    model=self._model,
                    messages=working_messages,
                    tools=tools if tools else None,
                )
                choice = response.choices[0]

                if choice.finish_reason == "tool_calls" or choice.message.tool_calls:
                    # Append the assistant's tool_calls message
                    working_messages.append(choice.message.model_dump())

                    for tool_call in choice.message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}

                        log.info("Calling MCP tool: %s(%s)", tool_name, tool_args)
                        result = await self._call_mcp_tool(tool_name, tool_args)

                        working_messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        })
                else:
                    # Text-only response — we're done
                    return choice.message.content or ""

            return "⚠️ Reached maximum tool-calling iterations. Please try a simpler request."

    async def _call_mcp_tool(self, name: str, arguments: dict[str, Any]) -> str:
        """Dispatch a single tool call to the MCP server."""
        try:
            result = await self._session.call_tool(name, arguments)
            if result.isError:
                error_text = "\n".join(
                    block.text for block in result.content if hasattr(block, "text")
                )
                return f"[Tool Error] {error_text}" if error_text else "[Tool Error] Unknown error"
            text_parts = [
                block.text for block in result.content if hasattr(block, "text")
            ]
            return "\n".join(text_parts) if text_parts else json.dumps({"status": "ok"})
        except Exception as exc:
            log.exception("MCP call_tool failed: %s", name)
            return f"[Tool Error] {exc}"

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    def list_resources_sync(self) -> list[dict[str, str]]:
        """List available MCP resources (synchronous)."""
        if not self._loop or not self._session:
            return []
        future = asyncio.run_coroutine_threadsafe(
            self._list_resources(), self._loop
        )
        try:
            return future.result(timeout=15)
        except Exception:
            return []

    async def _list_resources(self) -> list[dict[str, str]]:
        """List resources from the MCP server."""
        try:
            result = await self._session.list_resources()
            return [
                {"uri": str(r.uri), "name": r.name or "", "description": r.description or ""}
                for r in result.resources
            ]
        except Exception as exc:
            log.warning("list_resources failed: %s", exc)
            return []

    def read_resource_sync(self, uri: str) -> str:
        """Read a specific MCP resource by URI (synchronous)."""
        if not self._loop or not self._session:
            return ""
        future = asyncio.run_coroutine_threadsafe(
            self._read_resource(uri), self._loop
        )
        try:
            return future.result(timeout=15)
        except Exception:
            return ""

    async def _read_resource(self, uri: str) -> str:
        """Read a resource from the MCP server."""
        try:
            result = await self._session.read_resource(uri)
            if hasattr(result, "contents") and result.contents:
                parts = []
                for content in result.contents:
                    if hasattr(content, "text"):
                        parts.append(content.text)
                return "\n".join(parts)
            return ""
        except Exception as exc:
            log.warning("read_resource failed for %s: %s", uri, exc)
            return ""

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def list_prompts_sync(self) -> list[dict[str, Any]]:
        """List available MCP prompts (synchronous)."""
        if not self._loop or not self._session:
            return []
        future = asyncio.run_coroutine_threadsafe(
            self._list_prompts(), self._loop
        )
        try:
            return future.result(timeout=15)
        except Exception:
            return []

    async def _list_prompts(self) -> list[dict[str, Any]]:
        """List prompts from the MCP server."""
        try:
            result = await self._session.list_prompts()
            return [
                {
                    "name": p.name,
                    "description": p.description or "",
                    "arguments": [
                        {"name": a.name, "description": a.description or "", "required": a.required}
                        for a in (p.arguments or [])
                    ],
                }
                for p in result.prompts
            ]
        except Exception as exc:
            log.warning("list_prompts failed: %s", exc)
            return []

    def get_prompt_sync(self, name: str, arguments: dict[str, str] | None = None) -> str:
        """Retrieve a rendered MCP prompt by name (synchronous)."""
        if not self._loop or not self._session:
            return ""
        future = asyncio.run_coroutine_threadsafe(
            self._get_prompt(name, arguments or {}), self._loop
        )
        try:
            return future.result(timeout=15)
        except Exception:
            return ""

    async def _get_prompt(self, name: str, arguments: dict[str, str]) -> str:
        """Get a rendered prompt from the MCP server."""
        try:
            result = await self._session.get_prompt(name, arguments)
            parts = []
            for msg in result.messages:
                if hasattr(msg.content, "text"):
                    parts.append(msg.content.text)
                elif isinstance(msg.content, str):
                    parts.append(msg.content)
            return "\n\n".join(parts)
        except Exception as exc:
            log.warning("get_prompt failed for %s: %s", name, exc)
            return ""

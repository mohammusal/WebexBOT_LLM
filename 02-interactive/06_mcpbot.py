"""
Cisco Live 2026 - LABCOL-1007: Building Your First Webex Bot

MCP-Powered Webex Bot — connects to any MCP server via the generic bridge,
giving the bot access to organizational tools through natural language.

This file demonstrates:
  - MCP tool discovery (/tools)
  - Natural language → tool invocation (the agentic loop)
  - Write approval via Adaptive Cards (elicitation in chat)
  - Guided workflows via MCP prompts (/sync, /provision)
  - Resource-grounded LLM context
"""

import json
import logging
import os
import uuid

from dotenv import load_dotenv

from webex_bot.models.command import Command
from webex_bot.webex_bot import WebexBot

from mcp_bridge import MCPBridge

load_dotenv()

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

bot_token = os.getenv("BOT_TOKEN")
domain = os.getenv("DOMAIN")

server_command = os.getenv("MCP_SERVER_COMMAND", "python")
server_args = os.getenv("MCP_SERVER_ARGS", "-m,wxcc_mcp.server").split(",")
server_cwd = os.getenv("MCP_SERVER_CWD", ".")

MODEL = "gpt-4o-mini"
MAX_HISTORY = 20
MAX_RESPONSE_LENGTH = 7000

# ---------------------------------------------------------------------------
# MCP Bridge — spawned once at module load
# ---------------------------------------------------------------------------

bridge = MCPBridge(
    server_command=server_command,
    server_args=server_args,
    server_cwd=server_cwd,
    model=MODEL,
)
bridge.start()

# ---------------------------------------------------------------------------
# System prompt — grounded with MCP resources
# ---------------------------------------------------------------------------

BASE_SYSTEM_PROMPT = (
    "You are a helpful Webex assistant powered by MCP (Model Context Protocol). "
    "You have access to organizational tools for managing Webex Contact Center "
    "address books, entries, desktop profiles, and agents. "
    "Be concise and clear. When you use tools, explain what you found.\n\n"
    "IMPORTANT: For any write operations (create, update, delete, sync, assign), "
    "always call the tool with confirm=False first to get a preview. "
    "Never set confirm=True unless explicitly told to commit."
)


def build_system_prompt() -> str:
    """Build the full system prompt with MCP resources injected."""
    parts = [BASE_SYSTEM_PROMPT]

    resources = bridge.list_resources_sync()
    if resources:
        parts.append("\n## Available Organizational Data\n")
        for resource in resources:
            content = bridge.read_resource_sync(resource["uri"])
            if content:
                parts.append(f"### {resource['name'] or resource['uri']}\n{content}\n")

    return "\n".join(parts)


SYSTEM_PROMPT = build_system_prompt()

# ---------------------------------------------------------------------------
# Per-user state
# ---------------------------------------------------------------------------

conversations: dict[str, list[dict]] = {}
pending_approvals: dict[str, dict] = {}

# Write-tool detection patterns
WRITE_PREFIXES = ("tool_create_", "tool_update_", "tool_delete_",
                  "tool_sync_", "tool_assign_", "tool_bulk_")


def is_write_tool(name: str) -> bool:
    """Check if a tool name corresponds to a write operation."""
    return any(name.startswith(prefix) for prefix in WRITE_PREFIXES)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


class ChatMCPCommand(Command):
    """Main command: natural language → MCP tools via agentic loop."""

    def __init__(self):
        super().__init__(
            command_keyword="help",
            help_message="Chat with me — I can query and manage your Webex Contact Center via MCP tools.")

    def pre_execute(self, message, attachment_actions, activity):
        return "🤔 Thinking (calling MCP tools if needed)..."

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]

        if not message or not message.strip():
            return "Please type a message and I'll help using MCP-powered tools."

        if user_email not in conversations:
            conversations[user_email] = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        conversations[user_email].append({"role": "user", "content": message.strip()})

        result = bridge.run(conversations[user_email])

        conversations[user_email].append({"role": "assistant", "content": result})

        # Trim history
        history = conversations[user_email]
        while len(history) > 1 + MAX_HISTORY * 2:
            history.pop(1)
            history.pop(1)

        if len(result) > MAX_RESPONSE_LENGTH:
            result = result[:MAX_RESPONSE_LENGTH] + "\n\n⚠️ _Response was truncated._"

        return result


class ResetCommand(Command):
    """Clear conversation history."""

    def __init__(self):
        super().__init__(
            command_keyword="reset",
            help_message="Clear your conversation history and start fresh",
            exact_command_keyword_match=True)

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]
        conversations.pop(user_email, None)
        pending_approvals.pop(user_email, None)
        return "🔄 Conversation history cleared. Start fresh!"


class ToolsCommand(Command):
    """List available MCP tools grouped by type."""

    def __init__(self):
        super().__init__(
            command_keyword="tools",
            help_message="List all available MCP tools",
            exact_command_keyword_match=True)

    def execute(self, message, attachment_actions, activity):
        tools = bridge.get_openai_tools()
        if not tools:
            return "⚠️ No tools available from the connected MCP server."

        read_tools = []
        write_tools = []

        for tool in tools:
            name = tool["function"]["name"]
            desc = tool["function"]["description"]
            entry = f"• **{name}** — {desc}"
            if is_write_tool(name):
                write_tools.append(entry)
            else:
                read_tools.append(entry)

        parts = [f"🔧 **MCP Tools Available** ({len(tools)} total)\n"]

        if read_tools:
            parts.append("**📖 Read-only:**")
            parts.extend(read_tools)
            parts.append("")

        if write_tools:
            parts.append("**✏️ Write (approval required):**")
            parts.extend(write_tools)

        return "\n".join(parts)


class SyncCommand(Command):
    """Guided CRM sync workflow via MCP prompt."""

    def __init__(self):
        super().__init__(
            command_keyword="sync",
            help_message="Start a guided CRM → address book sync workflow",
            exact_command_keyword_match=True)

    def pre_execute(self, message, attachment_actions, activity):
        return "📋 Loading sync workflow from MCP server..."

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]

        # Get org_id from message or use a default hint
        org_id = message.strip() if message and message.strip() else "your-org-id"

        prompt_content = bridge.get_prompt_sync(
            "sync_crm_to_address_book",
            {"org_id": org_id}
        )

        if not prompt_content:
            available = bridge.list_prompts_sync()
            if available:
                names = ", ".join(p["name"] for p in available)
                return f"⚠️ Could not load sync prompt. Available prompts: {names}"
            return "⚠️ No prompts available from the MCP server."

        # Seed conversation with the prompt
        conversations[user_email] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"## Guided Workflow\n\n{prompt_content}"},
            {"role": "user", "content": f"Start the CRM sync workflow for org {org_id}. Guide me through it step by step."},
        ]

        result = bridge.run(conversations[user_email])
        conversations[user_email].append({"role": "assistant", "content": result})

        if len(result) > MAX_RESPONSE_LENGTH:
            result = result[:MAX_RESPONSE_LENGTH] + "\n\n⚠️ _Response was truncated._"

        return result


class ProvisionCommand(Command):
    """Guided provisioning workflow via MCP prompt."""

    def __init__(self):
        super().__init__(
            command_keyword="provision",
            help_message="Start a guided outbound dialing provisioning workflow",
            exact_command_keyword_match=True)

    def pre_execute(self, message, attachment_actions, activity):
        return "📋 Loading provisioning workflow from MCP server..."

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]

        org_id = message.strip() if message and message.strip() else "your-org-id"

        prompt_content = bridge.get_prompt_sync(
            "provision_outbound_dialing",
            {"org_id": org_id}
        )

        if not prompt_content:
            available = bridge.list_prompts_sync()
            if available:
                names = ", ".join(p["name"] for p in available)
                return f"⚠️ Could not load provision prompt. Available prompts: {names}"
            return "⚠️ No prompts available from the MCP server."

        conversations[user_email] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"## Guided Workflow\n\n{prompt_content}"},
            {"role": "user", "content": f"Start the outbound dialing provisioning workflow for org {org_id}. Guide me step by step."},
        ]

        result = bridge.run(conversations[user_email])
        conversations[user_email].append({"role": "assistant", "content": result})

        if len(result) > MAX_RESPONSE_LENGTH:
            result = result[:MAX_RESPONSE_LENGTH] + "\n\n⚠️ _Response was truncated._"

        return result


class ApproveCommand(Command):
    """Handle Adaptive Card approval/decline callbacks."""

    def __init__(self):
        super().__init__(
            card_callback_keyword="mcp_approval_callback",
            help_message="Handle write approval")

    def execute(self, message, attachment_actions, activity):
        user_email = activity["actor"]["emailAddress"]

        if not attachment_actions or not attachment_actions.inputs:
            return "⚠️ No approval data received."

        inputs = attachment_actions.inputs
        action = inputs.get("action", "")
        approval_id = inputs.get("approval_id", "")

        if approval_id not in pending_approvals:
            return "⚠️ This approval has expired or was already handled."

        approval = pending_approvals.pop(approval_id)

        if action == "approve":
            # Re-call the tool with confirm=True
            tool_name = approval["tool_name"]
            tool_args = approval["tool_args"]
            tool_args["confirm"] = True

            # Run the confirmed call through the bridge
            confirm_messages = approval.get("messages", [])
            confirm_messages.append({
                "role": "user",
                "content": f"The user approved the write. Now call {tool_name} with confirm=True to commit the change."
            })

            result = bridge.run(confirm_messages)

            # Update conversation
            if user_email in conversations:
                conversations[user_email].append({"role": "assistant", "content": result})

            return f"✅ **Approved and committed.**\n\n{result}"

        else:
            return "❌ **Declined.** No changes were made."


# ---------------------------------------------------------------------------
# Adaptive Card builder for write approvals
# ---------------------------------------------------------------------------


def build_approval_card(preview_text: str, tool_name: str, approval_id: str) -> dict:
    """Build an Adaptive Card for write approval."""
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ Write Operation Preview",
                    "weight": "bolder",
                    "size": "medium",
                },
                {
                    "type": "TextBlock",
                    "text": f"**Tool:** {tool_name}",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": preview_text[:1000],
                    "wrap": True,
                    "fontType": "monospace",
                    "size": "small",
                },
                {
                    "type": "TextBlock",
                    "text": "Do you want to commit this change?",
                    "wrap": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "✅ Approve",
                    "data": {
                        "callback_keyword": "mcp_approval_callback",
                        "action": "approve",
                        "approval_id": approval_id,
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Decline",
                    "data": {
                        "callback_keyword": "mcp_approval_callback",
                        "action": "decline",
                        "approval_id": approval_id,
                    },
                },
            ],
        },
    }


# ---------------------------------------------------------------------------
# Bot setup and run
# ---------------------------------------------------------------------------

bot = WebexBot(
    teams_bot_token=bot_token,
    bot_name="MCP Bot",
    approved_domains=domain,
    include_demo_commands=False,
    help_command=ChatMCPCommand(),
)

bot.add_command(ResetCommand())
bot.add_command(ToolsCommand())
bot.add_command(SyncCommand())
bot.add_command(ProvisionCommand())
bot.add_command(ApproveCommand())

log.info("MCP Bot starting — connected to MCP server at %s", server_cwd)
bot.run()

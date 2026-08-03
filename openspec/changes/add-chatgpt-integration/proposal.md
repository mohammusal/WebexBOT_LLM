## Why

The Webex bot currently handles only hardcoded keyword commands (echo, help, provisioning). Users want to have free-form conversations with ChatGPT directly through Webex — turning the bot into an AI assistant without rebuilding the existing architecture. The OpenAI Python SDK is already installed and an API key is available.

## What Changes

- Add a new `Command` subclass that forwards the user's message to OpenAI's Chat Completions API and returns the response.
- Maintain per-user conversation history (in-memory dict) so follow-up questions have context.
- Wire the new command as the bot's `help_command` (fallback) so **every** unmatched message goes to ChatGPT — no keyword required.
- Add a `reset` keyword to let users clear their conversation history.
- Add `OPENAI_API_KEY` to `.env` and `openai` to `requirements.txt`.
- Create a new bot entry point (`02-interactive/05_llmbot.py`) following the existing file naming convention.

## Capabilities

### New Capabilities
- `chatgpt-conversation`: Free-form, stateful ChatGPT conversation through the Webex bot — receiving any user message, forwarding it to OpenAI, maintaining per-user history, and returning the response.

### Modified Capabilities
<!-- No existing specs are being modified — this is a purely additive feature. -->

## Impact

- **New file**: `02-interactive/05_llmbot.py` (new bot entry point, ~60 lines)
- **Modified files**: `.env` (add `OPENAI_API_KEY`), `requirements.txt` (add `openai`)
- **Dependencies**: `openai` Python package (already installed on system, v2.46.0)
- **APIs**: OpenAI Chat Completions API (`gpt-4o-mini` default)
- **No breaking changes** to existing bot scripts — all `01_`–`04_` files remain untouched.

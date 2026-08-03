## Context

The project uses the `webex_bot` framework (v1.3.1) which routes incoming messages through a `Command` class hierarchy. When no registered command keyword matches, the framework falls through to `self.help_command` (see `webex_bot.py` line 273-275). The `WebexBot` constructor accepts a `help_command` parameter to override this fallback. See proposal.md for motivation.

Existing bot scripts (`01_`–`04_`) in `02-interactive/` each define their own `Command` subclasses and boot a `WebexBot` — this change follows the same pattern in a new `05_llmbot.py`.

## Goals / Non-Goals

**Goals:**
- Every user message goes to ChatGPT with zero keyword friction
- Conversation context persists across messages within a bot session
- Minimal code (~60 lines), no new architectural patterns

**Non-Goals:**
- Persistent storage (database/file) for conversation history — in-memory is sufficient
- Streaming responses from OpenAI
- Multi-model support or model switching
- Modifying existing bot scripts

## Decisions

### 1. Override `help_command` for catch-all routing

**Choice**: Pass our `ChatGPTCommand` as the `help_command` parameter to `WebexBot()` and set `include_demo_commands=False`.

**Why**: The framework's fallback path (`if not command: command = self.help_command`) is the only mechanism for catch-all behavior without modifying the library. This is a single-line wiring change.

**Alternative considered**: Using an empty-string `command_keyword` — rejected because `""` is falsy in Python, so the framework skips keyword matching for it entirely (line 250: `if ... c.command_keyword:`).

### 2. In-memory dict for conversation state

**Choice**: A module-level `dict[str, list[dict]]` mapping user email → OpenAI message list.

**Why**: Simplest possible approach. The bot is a single-process, long-running script. No serialization, no database, no external dependencies. State resets when the bot restarts, which is acceptable for this use case.

**Alternative considered**: SQLite or Redis — overkill for a lab/demo bot.

### 3. Extract user email from `activity` object

**Choice**: Use `activity['actor']['emailAddress']` inside `execute()` to identify the user.

**Why**: The `execute()` signature is `execute(self, message, attachment_actions, activity)`. The `activity` dict reliably contains the actor's email. The `attachment_actions` parameter (which is actually the `teams_message` object in the non-card path) also has `.personEmail`, but `activity` is more consistent across card/non-card paths.

### 4. Model choice: `gpt-4o-mini`

**Choice**: Default to `gpt-4o-mini` for cost efficiency.

**Why**: This is a demo/lab bot. `gpt-4o-mini` is fast, cheap, and good enough. The model name is a constant at the top of the file, trivial to change.

### 5. Separate `ResetCommand` for history clearing

**Choice**: A small `Command` subclass with `command_keyword="reset"` and `exact_command_keyword_match=True`, registered via `bot.add_command()`.

**Why**: This keeps "reset" as a proper keyword command that the framework routes before falling through to the ChatGPT catch-all. Clean separation of concerns.

## Risks / Trade-offs

- **Memory growth** → Mitigated by capping history at 20 message pairs per user. For a lab bot with few users this is negligible.
- **OpenAI latency (2-10s)** → Mitigated by using `pre_execute()` to send a "Thinking..." indicator before calling the API.
- **Webex message size limit (~7439 bytes)** → Mitigated by truncating responses over 7000 characters.
- **API key exposure** → Key stored in `.env`, loaded via `dotenv`, read by the `openai` library from the environment variable `OPENAI_API_KEY`. Never logged or included in responses.
- **No persistence** → Conversation history is lost on bot restart. Acceptable for demo/lab scope.

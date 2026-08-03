## 1. Configuration

- [x] 1.1 Add `OPENAI_API_KEY` entry to `.env` (placeholder value for the user to fill in)
- [x] 1.2 Add `openai` to `requirements.txt`

## 2. Core Implementation

- [x] 2.1 Create `02-interactive/05_llmbot.py` with imports, env loading, and constants (`SYSTEM_PROMPT`, `MODEL`, `MAX_HISTORY`, `MAX_RESPONSE_LENGTH`, `conversations` dict)
- [x] 2.2 Implement `ChatGPTCommand(Command)` — `__init__` with `command_keyword="help"`, `pre_execute()` returning "🤔 Thinking...", and `execute()` that: extracts user email from `activity`, manages per-user history, calls OpenAI Chat Completions, appends response, truncates history, handles errors, and enforces response length limit
- [x] 2.3 Implement `ResetCommand(Command)` — `__init__` with `command_keyword="reset"` and `exact_command_keyword_match=True`, `execute()` that clears the user's conversation history and returns a confirmation

## 3. Bot Wiring

- [x] 3.1 Wire `WebexBot` with `help_command=ChatGPTCommand()`, `include_demo_commands=False`, `approved_domains=domain`, and register `ResetCommand` via `bot.add_command()`
- [x] 3.2 Add `bot.run()` at the end of the file

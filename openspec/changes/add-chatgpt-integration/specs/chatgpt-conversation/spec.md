## Purpose

Enables free-form, stateful ChatGPT conversations through the Webex bot so users can ask any question without keyword prefixes and receive contextual follow-up responses.

## ADDED Requirements

### Requirement: Catch-all message forwarding
The bot SHALL forward every incoming user message that does not match another registered command to the OpenAI Chat Completions API and return the generated response to the user in the same Webex conversation.

#### Scenario: User sends a free-form question
- **WHEN** a user sends "What is BGP?" in a 1-on-1 chat with the bot
- **THEN** the bot sends the message to OpenAI and replies with the model's answer

#### Scenario: User sends a message in a group space
- **WHEN** a user mentions the bot with "explain subnetting" in a group space
- **THEN** the bot forwards "explain subnetting" to OpenAI and replies in that space

### Requirement: Per-user conversation history
The bot SHALL maintain a separate conversation history for each user (keyed by email address) so that follow-up questions have context from previous exchanges in the same session.

#### Scenario: Follow-up question with context
- **WHEN** a user asks "What is OSPF?" and then asks "How does it compare to EIGRP?"
- **THEN** the second response references OSPF from the prior exchange without the user repeating context

#### Scenario: Separate users have independent histories
- **WHEN** user A asks "What is BGP?" and user B asks "What is DNS?"
- **THEN** each user's conversation history is independent — user B's response does not reference BGP

### Requirement: Conversation history limit
The bot SHALL cap per-user conversation history to a configurable maximum number of message pairs. When the limit is exceeded, the oldest messages (excluding the system prompt) SHALL be removed.

#### Scenario: History exceeds limit
- **WHEN** a user has exchanged 20 message pairs and sends a 21st message
- **THEN** the oldest user/assistant pair is removed before sending the request to OpenAI

### Requirement: Conversation reset
The bot SHALL provide a `reset` command that clears the calling user's conversation history and confirms the reset.

#### Scenario: User resets conversation
- **WHEN** a user sends "reset"
- **THEN** the bot clears that user's history and replies with a confirmation message

### Requirement: Error handling
The bot SHALL return a user-friendly error message when the OpenAI API call fails, without exposing internal details such as API keys or stack traces.

#### Scenario: OpenAI API error
- **WHEN** the OpenAI API returns an error (rate limit, timeout, invalid key)
- **THEN** the bot replies with a generic error message indicating the request could not be processed

### Requirement: Response length safety
The bot SHALL truncate or segment responses that exceed the Webex message size limit (~7000 characters) so that no message delivery fails silently.

#### Scenario: Long response from OpenAI
- **WHEN** OpenAI returns a response longer than 7000 characters
- **THEN** the bot truncates the response and appends a notice that the output was shortened

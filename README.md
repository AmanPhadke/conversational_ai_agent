# AutoStream Sales Agent

A conversational AI agent that converts social media conversations into qualified business leads. Built with AutoGen and Google Gemini.

## How to Run the Project Locally

### Prerequisites
- Python 3.9 or higher
- LLM API key

### Setup Steps

1. **Clone the repository and install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create a `.env` file in the project root:**
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Create `llm_config.json` file:**
   ```json
   {
     "config_list": [
       {
         "model": "gemini-1.5-flash",
         "api_key": "${GEMINI_API_KEY}",
         "api_type": "google"
       }
     ]
   }
   ```

4. **Ensure `knowledge_base.json` is in the project directory** with pricing and policy information.

5. **Run the chatbot:**
   ```bash
   python agent.py
   ```

6. **Start a conversation:**
   ```
   Autostream Chatbot (type "exit" to quit)
   
   You: Hi, what are your pricing options?
   Bot: [Response with pricing information from knowledge base]
   
   You: The Pro plan sounds good, I want to sign up for my YouTube channel
   Bot: Great! To complete your signup, I need your name and email.
   
   You: My name is John Smith and my email is john@example.com
   Bot: [Returns JSON with captured lead information]
   Lead captured successfully: {name}, {email}, {platform}
   Information Stored Successfully
   ```

---

## Architecture Explanation

### Why I used Autogen?

I chose Autogen was chosen over Langgraph because it provides a simpler, more production-ready framework for this use case. AutoGen's `AssistantAgent` and `UserProxyAgent` naturally handle conversation state and message history without requiring explicit state machine definitions(I used the older version of autogen as it was easier to import these autogen sublibraries). The framework works great at:

- **Automatic message routing** between user and assistant
- **Built-in tool calling** for functions like `mock_lead_capture()`
- **Seamless LLM integration** with multiple providers (Google, OpenAI, Claude, etc.)
- **Minimal boilerplate** compared to LangGraph's explicit state management

LangGraph is more powerful but overkill for this straightforward intent-based workflow.

### State Management

State is managed through two mechanisms:

1. **Temporary Conversation History** (`messages` list):
   - Accumulates all user and assistant messages across turns
   - Passed to the LLM each turn for context
   - Allows agent to remember entire conversation flow

2. **User State Dictionary** (`user_state`):
   - Stores extracted fields: `name`, `email`, `platform`
   - Updated by regex extraction on each user input
   - Passed to LLM as context in state_info
   - Prevents re-asking for already-provided information

The system extracts structured data (email, name) using regex patterns before sending to the LLM. This keeps the agent focused on intent detection and conversation flow instead of pattern matching. The LLM receives the current state and decides whether to ask for missing fields or proceed with lead capture.

---

## WhatsApp Integration with Webhooks

### Architecture Overview

For WhatsApp integration I would use a webhook-based architecture(as mentioned in the assessment pdf):

```
WhatsApp Business API
        ↓
   [Webhook Server]
        ↓
   [Session Manager (such as Redis)]
        ↓
   [AutoStream Agent]
        ↓
   [Lead Database]
```

### Implementation Steps

1. **Webhook Setup** - Register a webhook URL (e.g., `https://your-domain.com/webhooks/whatsapp`) in Meta's dashboard that receives all incoming WhatsApp messages.
 
2. **Message Handling** - When a user sends a message on WhatsApp, Meta sends a POST request to your webhook with the message content and sender's phone number.
 
3. **Session Management** - Store each user's conversation history in a session store (probably Redis database) using their phone number as the key. This allows the agent to maintain context across multiple WhatsApp messages over time.
 
4. **Agent Processing** - Pass the incoming message and conversation history to the AutoStream agent (same logic as the chatbot). The agent detects intent, retrieves knowledge base info, and collects lead details.
 
5. **Response Delivery** - Send the agent's response back to the user via WhatsApp Business API. If a lead is captured (all three fields collected), trigger the lead capture function and notify your backend systems.
 
6. **State Persistence** - The regex-based state extraction (email, name, platform) works identically. Each message updates the user's state in the session store. After lead capture, you can reset the conversation or archive it.
 
This approach is easy to scale easily. Each incoming WhatsApp message is a separate webhook call and session management handles concurrent conversations across thousands of users.

---

## Project Structure

```
autostream-agent/
├── agent.py        # Main agent code
├── knowledge_base.json     # Pricing and policy data
├── llm_config.json         # LLM configuration
├── requirements.txt        # Dependencies
├── .env_template           # API keys
├── README.md               # This file
└── agent_alt.py            # Alternate approach using genai api call
```

## Dependencies

See `requirements.txt` for full list. Core dependencies:
- `pyautogen` - Multi-agent conversation framework
- `google-generativeai` - Google Gemini API
- `python-dotenv` - Environment variable management
- `regex` - Pattern matching for email/name extraction

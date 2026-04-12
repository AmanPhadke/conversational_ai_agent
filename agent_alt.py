from dotenv import load_dotenv
import json
import google.generativeai as genai
import os

load_dotenv()


with open("llm_config.json", "r", encoding="utf-8") as file:
        config = json.load(file)

llm_config = json.dumps(config, indent = 2)
api_key = os.getenv("GEMINI_API_KEY")
llm_config["api_key"] = api_key


if not API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY in environment or .env file.")

with open("knowledge_base.json", "r", encoding="utf-8") as file:
        data = json.load(file)

knowledge_base = json.dumps(data, indent=2)


system_prompt = f"""You are a helpful sales assistant for AutoStream, a video editing SaaS platform.

You have access to this knowledge base:
{kb_str}

Your responsibilities:
1. Answer questions about pricing, features, and policies using the knowledge base
2. Be professional and helpful
3. When a user shows buying intent (wants to purchase, mentions their platform, etc.):
   - Collect their NAME
   - Collect their EMAIL
   - Collect their CREATOR PLATFORM (YouTube, Instagram, TikTok, etc.)
   - Once you have all THREE pieces of information, call the mock_lead_capture function
4. Do NOT call the function until you have ALL THREE pieces of information
5. If the user asks something unrelated to AutoStream, politely redirect them

Keep responses concise and professional."""

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    "gemini-3.1-flash-lite-preview"
    # system_instruction = system_instruction
)

conversation = model.start_chat()

def chat(user_query):
    prompt = ("""
    If it is a greeting greet the user and be friendly but also keep it professional you are a chatbot of a company so only answer relevant queries if the user is just using you for fun tell then that you are a company bot and can't answer the query\n
    """
    f'User Query:\n {user_query}'
    )
    answer = conversation.send_message(prompt)
    return answer.text
    
def intent_detection(user_query):
    prompt = f"""
    Classify this message into one of these intents: GREETING, PRICING_INQUIRY, or HIGH_INTENT_BUY, Respond with ONLY the intent name, nothing else
    User input: "{user_query}"
    """
    
    response = conversation.send_message(prompt)
    
    try:
        return response.text
    except:
        return {"intent": "unknown"}


def pricing_kb(user_query, knowldge_base):
    
    prompt = ("""
    For questions about plans, pricing, or policies, rely on this knowledge. If something is not in the knowledge base, say you do not have that information.\n
    """
    f'Knowledge Base : {knowldge_base}'
    f'User Query: {user_query}'
    )

    answer = conversation.send_message(prompt)
    return answer.text
    
def user_info(users_db):
    email = input("What is your email?: ").strip()
    
    if email in users_db:
        print("User already exists. Fetching data...\n")
        user = users_db[email]
        return user, user['name'], user['email'], user['platform']

    user = {}
    user['email'] = email
    user['name'] = input("Enter your name: ").strip()
    user['platform'] = input("Enter your platform (YouTube, Instagram, etc.): ").strip()
    
    if not user['email'] or not user['name'] or not user['platform']:
        print("Error: All fields (email, name, platform) are required!")
        return None, None, None, None
    
    users_db[email] = user
    
    return user, user['name'], user['email'], user['platform']

def mock_lead_capture(name, email, platform):
    print(f"Lead captured successfully: {name}, {email}, {platform}")

while True:
    user_query = input("Please enter your query: ").strip()

    if user_query.lower() == 'exit':
        break
    if not user_query:
        continue

    intent = intent_detection(user_query)
    if intent == 'GREETING':
        print(chat(user_query))

    elif intent == 'PRICING_INQUIRY':
        print(pricing_kb(user_query, knowledge_base))
    
    elif intent == 'HIGH_INTENT_BUY':
        info, name, email, platform = user_info(users_db)
        
        if name and email and platform:
            mock_lead_capture(name, email, platform)
        else:
            print("Could not complete lead capture. Please try again.\n")
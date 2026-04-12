import os
from dotenv import load_dotenv
import json
from autogen import AssistantAgent, UserProxyAgent
import re

load_dotenv()

#llm_config extraction
with open('llm_config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)


#getting api key
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    raise SystemExit('Missing GEMINI_API_KEY')


#knowledge base extraction
with open('knowledge_base.json', 'r', encoding='utf-8') as file: 
    data = json.load(file) 
    
knowledge_base = json.dumps(data, indent=2)

#managing user state
user_state = {
    'name': None,
    'email': None,
    'platform': None
}

#setting email regex
def extract_email(text):
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if match:
        return match.group() 
    return None

#state management
def update_state(text):
    text_lower = text.lower()

    # email detection
    email = extract_email(text)
    if email and not user_state['email']:
        user_state['email'] = email

    # platform detection
    if 'youtube' in text_lower:
        user_state['platform'] = 'YouTube'
    elif 'instagram' in text_lower:
        user_state['platform'] = 'Instagram'
    elif 'tiktok' in text_lower:
        user_state['platform'] = 'TikTok'

    # name detection
    if not user_state['name']:
        name_patterns = [
            r'my name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'i\'m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'call me\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'i am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                user_state['name'] = match.group(1).title()
                break

#providing main system prompt
system_prompt = (
    'You are a sales assistant for AutoStream, an AI-powered video editing platform for content creators.\n'
    '\n'
    'Your responsibilities:\n'
    '1. GREETING - Answer greetings professionally and keep it brief.\n'
    '2. PRICING_INQUIRY - Answer questions about pricing and features using the knowledge base.\n'
    '3. HIGH_INTENT_BUY - When user wants to purchase or sign up:\n'
    '   - Collect: Name, Email, Creator Platform\n'
    '   - Ask only for missing information\n'
    '   - Never ask twice for the same info\n'
    '   - Email must be valid (contain @)\n'
    '\n'
    'Lead Capture Rules:\n'
    'Only return this JSON when you have collected ALL THREE fields (name AND email AND platform):\n'
    '{\n'
    '  "action": "lead_captured",\n'
    '  "name": "...",\n'
    '  "email": "...",\n'
    '  "platform": "..."\n'
    '}\n'
    '\n'
    'Do not return JSON prematurely or return anything else.\n'
    '\n'
    f'Knowledge Base:\n{knowledge_base}\n'
    '\n'
    'Answer only based on this knowledge base. Do not answer questions outside of this.'
)

#adding configuration
llm_config = {
    'config_list': [
        {
            'model': config['config_list'][0]['model'],
            'api_key': api_key,
            'api_type': config['config_list'][0]['api_type'],
        }
    ],
    'temperature': 0, 
}

#mock function
def mock_lead_capture(name, email, platform):
    print(f'Lead captured successfully: {name}, {email}, {platform}')
    return {'status': 'success'}

#appending into mock function
def append_capture(response_text):
    try:
        data = json.loads(response_text)
        if data.get('action') == 'lead_captured':
            mock_lead_capture(
                data["name"],
                data["email"],
                data["platform"]
            )
            return True
    except:
        pass
    
    return False

#assistant agent
assistant = AssistantAgent(
    name='assistant',
    system_message=system_prompt,
    llm_config=llm_config,
    function_map={'mock_lead_capture': mock_lead_capture},
)

#user agent
user = UserProxyAgent(
    name='user',
    human_input_mode='ALWAYS',
)


if __name__ == '__main__':
    print('Autostream Chatbot (type "exit" to quit)\n')

    #temporary message storage
    messages = []


    while True:
        user_input = input('You: ')

        if user_input.lower() == 'exit':
            break

        #updating state after every prompt
        update_state(user_input)

        #known info
        state_info = f'''Known user info:
            Name: {user_state["name"]}
            Email: {user_state["email"]}
            Platform: {user_state["platform"]}
        '''

        messages.append({
            'role': 'user',
            'content': state_info + '\n\nUser: ' + user_input
        })

        response = assistant.generate_reply(messages = messages)

        if isinstance(response, dict):
            bot_text = response.get('content')
        else:
            bot_text = response

        if bot_text:
            print(f'Bot: {bot_text}')
            messages.append({'role': 'assistant', 'content': bot_text})

            if append_capture(bot_text):

                print('Information Stored Successfully')

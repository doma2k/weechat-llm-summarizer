import weechat
import json
import urllib.request
import urllib.error
from datetime import datetime
import os

SCRIPT_NAME = "llm_summarizer"
SCRIPT_AUTHOR = "anton-doltan"
SCRIPT_VERSION = "1.2"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Summarize chat with local LLM"

config_defaults = {
    "llm_url": "http://localhost:11434/api/generate",
    "llm_model": "llama3.2:3b", 
    "max_history_lines": "50",
    "temperature": "0.7",
    "prompt_file": "summary_prompt.txt",
}

buffer_history = {}

def init_config():
    for key, value in config_defaults.items():
        if not weechat.config_is_set_plugin(key):
            weechat.config_set_plugin(key, value)

def get_config(key):
    return weechat.config_get_plugin(key)

def load_prompt_template(history_text):
    """Load prompt from external file - fallback to default if missing"""
    try:
        # Get script directory using weechat info
        weechat_dir = weechat.info_get("weechat_dir", "")
        script_dir = os.path.join(weechat_dir, "python")
        prompt_file = os.path.join(script_dir, get_config("prompt_file"))
        
        with open(prompt_file, 'r') as f:
            template = f.read()
        
        # Replace placeholder
        prompt = template.replace("{{history}}", history_text)
        return prompt
        
    except FileNotFoundError:
        # Fallback to the simple prompt that was working
        return f"""Please provide a concise summary of this chat conversation:

{history_text}

Summary:"""
    except Exception as e:
        weechat.prnt("", f"Error loading prompt file: {e}")
        return f"""Please provide a concise summary of this chat conversation:

{history_text}

Summary:"""

def call_llm(prompt):
    try:
        url = get_config("llm_url")
        model = get_config("llm_model")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url, 
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "No response from LLM")
            
    except urllib.error.URLError as e:
        return f"URL Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def add_to_history(buffer_name, prefix, message):
    if buffer_name not in buffer_history:
        buffer_history[buffer_name] = []
    
    timestamp = datetime.now().strftime("%H:%M")
    entry = f"[{timestamp}] {prefix}: {message}"
    buffer_history[buffer_name].append(entry)
    
    max_lines = int(get_config("max_history_lines"))
    if len(buffer_history[buffer_name]) > max_lines:
        buffer_history[buffer_name] = buffer_history[buffer_name][-max_lines:]

def get_history_text(buffer_name):
    if buffer_name not in buffer_history or not buffer_history[buffer_name]:
        return "No history available."
    
    return "\n".join(buffer_history[buffer_name])

def generate_summary(buffer):
    buffer_name = weechat.buffer_get_string(buffer, "name")
    history_text = get_history_text(buffer_name)
    
    if history_text == "No history available.":
        weechat.prnt(buffer, "No recent history to summarize.")
        return
    
    weechat.prnt(buffer, "Generating summary...")
    
    # Use external prompt template with fallback
    prompt = load_prompt_template(history_text)
    
    summary = call_llm(prompt)
    
    # Green text with spacing
    weechat.prnt(buffer, "")
    for line in summary.split('\n'):
        if line.strip():
            weechat.prnt(buffer, weechat.color("green") + line + weechat.color("reset"))
    weechat.prnt(buffer, "")

def message_handler(data, buffer, date, tags, displayed, highlight, prefix, message):
    buffer_name = weechat.buffer_get_string(buffer, "name")
    add_to_history(buffer_name, prefix, message)
    return weechat.WEECHAT_RC_OK

def summary_command(data, buffer, args):
    generate_summary(buffer)
    return weechat.WEECHAT_RC_OK

if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
    init_config()
    weechat.hook_print("", "irc_privmsg", "", 1, "message_handler", "")
    weechat.hook_command("summary", "Generate chat summary using LLM", "", "", "", "summary_command", "")
    weechat.prnt("", "LLM Summarizer loaded! Use /summary to generate summaries.")
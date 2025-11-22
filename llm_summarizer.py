import weechat
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import os
import re

SCRIPT_NAME = "llm_summarizer"
SCRIPT_AUTHOR = "anton-doltan"
SCRIPT_VERSION = "1.4"
SCRIPT_LICENSE = "MIT"
SCRIPT_DESC = "Summarize chat with local LLM"

config_defaults = {
    "llm_url": "http://localhost:11434/api/generate",
    "llm_model": "llama3.2:3b", 
    "max_history_lines": "150",
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
    
    timestamp = datetime.now()
    entry = {
        "timestamp": timestamp,
        "text": f"[{timestamp.strftime('%H:%M')}] {prefix}: {message}"
    }
    buffer_history[buffer_name].append(entry)
    
    max_lines = int(get_config("max_history_lines"))
    if len(buffer_history[buffer_name]) > max_lines:
        buffer_history[buffer_name] = buffer_history[buffer_name][-max_lines:]

def parse_time_argument(time_arg):
    """Parse time arguments like 5m, 5h, 30m, 2h etc."""
    if not time_arg:
        return None
    
    match = re.match(r'^(\d+)([mh])$', time_arg.lower())
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
    
    return None

def get_history_text(buffer_name, time_delta=None, line_count=None):
    if buffer_name not in buffer_history or not buffer_history[buffer_name]:
        return "No history available."
    
    history_entries = buffer_history[buffer_name]
    
    # Filter by time if time_delta is provided
    if time_delta:
        cutoff_time = datetime.now() - time_delta
        filtered_entries = [entry for entry in history_entries if entry["timestamp"] >= cutoff_time]
        if not filtered_entries:
            return "No history available for the specified time period."
    # Filter by line count if line_count is provided
    elif line_count:
        filtered_entries = history_entries[-line_count:]
        if not filtered_entries:
            return "No history available."
    # Otherwise, return all history
    else:
        filtered_entries = history_entries
    
    return "\n".join(entry["text"] for entry in filtered_entries)

def get_buffer_stats(buffer_name):
    """Get statistics for current buffer history"""
    if buffer_name not in buffer_history or not buffer_history[buffer_name]:
        return None
    
    history = buffer_history[buffer_name]
    line_count = len(history)
    
    if line_count > 0:
        oldest_msg = history[0]["timestamp"]
        newest_msg = history[-1]["timestamp"]
        time_span = newest_msg - oldest_msg
        
        return {
            "line_count": line_count,
            "oldest_msg": oldest_msg,
            "newest_msg": newest_msg,
            "time_span": time_span
        }
    
    return None

def show_buffer_stats(buffer):
    """Display statistics for current buffer"""
    buffer_name = weechat.buffer_get_string(buffer, "name")
    stats = get_buffer_stats(buffer_name)
    
    weechat.prnt(buffer, "")
    weechat.prnt(buffer, "=== LLM Summarizer History Stats ===")
    
    if stats:
        weechat.prnt(buffer, f"Stored messages: {stats['line_count']}")
        weechat.prnt(buffer, f"Oldest message: {stats['oldest_msg'].strftime('%Y-%m-%d %H:%M:%S')}")
        weechat.prnt(buffer, f"Newest message: {stats['newest_msg'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate time span in human readable format
        total_seconds = stats['time_span'].total_seconds()
        if total_seconds < 60:
            time_span_str = f"{total_seconds:.0f} seconds"
        elif total_seconds < 3600:
            time_span_str = f"{total_seconds/60:.1f} minutes"
        else:
            time_span_str = f"{total_seconds/3600:.1f} hours"
        
        weechat.prnt(buffer, f"Time span: {time_span_str}")
        max_lines = int(get_config("max_history_lines"))
        weechat.prnt(buffer, f"Max storage: {max_lines} lines")
    else:
        weechat.prnt(buffer, "No history stored for this buffer")
    
    # Show global stats
    total_buffers = len(buffer_history)
    total_messages = sum(len(history) for history in buffer_history.values())
    weechat.prnt(buffer, f"Total buffers with history: {total_buffers}")
    weechat.prnt(buffer, f"Total messages stored: {total_messages}")
    weechat.prnt(buffer, "===================================")
    weechat.prnt(buffer, "")

def clean_buffer_history(buffer, buffer_name=None):
    """Clean history for current buffer or specific buffer"""
    if buffer_name is None:
        buffer_name = weechat.buffer_get_string(buffer, "name")
    
    if buffer_name in buffer_history:
        deleted_count = len(buffer_history[buffer_name])
        del buffer_history[buffer_name]
        weechat.prnt(buffer, f"✓ Cleared {deleted_count} messages from {buffer_name} history")
        return deleted_count
    else:
        weechat.prnt(buffer, f"No history found for {buffer_name}")
        return 0

def clean_all_history(buffer):
    """Clean history for all buffers"""
    total_buffers = len(buffer_history)
    total_messages = sum(len(history) for history in buffer_history.values())
    
    buffer_history.clear()
    
    weechat.prnt(buffer, "")
    weechat.prnt(buffer, f"✓ Cleared all history from {total_buffers} buffers ({total_messages} messages total)")
    weechat.prnt(buffer, "")

def generate_summary(buffer, time_delta=None, line_count=None):
    buffer_name = weechat.buffer_get_string(buffer, "name")
    
    if time_delta:
        time_desc = f"last {time_delta.total_seconds()/60:.0f} minutes" if time_delta.total_seconds() < 3600 else f"last {time_delta.total_seconds()/3600:.0f} hours"
        history_text = get_history_text(buffer_name, time_delta=time_delta)
        weechat.prnt(buffer, f"Generating summary for {time_desc}...")
    elif line_count:
        history_text = get_history_text(buffer_name, line_count=line_count)
        weechat.prnt(buffer, f"Generating summary for last {line_count} lines...")
    else:
        history_text = get_history_text(buffer_name)
        weechat.prnt(buffer, "Generating summary for all recent history...")
    
    if history_text == "No history available." or history_text.startswith("No history available"):
        weechat.prnt(buffer, history_text)
        return
    
    weechat.prnt(buffer, "")
    
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
    if not args:
        # No arguments - use all history
        generate_summary(buffer)
    else:
        # Try to parse as time argument first (5m, 5h, etc.)
        time_delta = parse_time_argument(args)
        if time_delta:
            generate_summary(buffer, time_delta=time_delta)
        else:
            # Try to parse as line count
            try:
                line_count = int(args)
                if line_count > 0:
                    generate_summary(buffer, line_count=line_count)
                else:
                    weechat.prnt(buffer, "Error: Line count must be a positive number")
            except ValueError:
                weechat.prnt(buffer, "Error: Invalid argument. Use /sum [5m|5h|5] for time-based or line-based summary")
    
    return weechat.WEECHAT_RC_OK

def stats_command(data, buffer, args):
    """Show history statistics for current buffer"""
    show_buffer_stats(buffer)
    return weechat.WEECHAT_RC_OK

def clean_command(data, buffer, args):
    """Clean history - usage: /sumclean [all|buffer_name]"""
    if not args:
        # Clean current buffer
        clean_buffer_history(buffer)
    elif args.lower() == "all":
        # Clean all buffers
        clean_all_history(buffer)
    else:
        # Clean specific buffer by name
        clean_buffer_history(buffer, args)
    
    return weechat.WEECHAT_RC_OK

if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
    init_config()
    weechat.hook_print("", "irc_privmsg", "", 1, "message_handler", "")
    
    # Main summary command
    weechat.hook_command(
        "sum", 
        "Generate chat summary using LLM", 
        "[5m|5h|5]",
        "5m: last 5 minutes\n5h: last 5 hours\n5: last 5 lines\nno argument: all recent history", 
        "5m|5h|%(lines)",
        "summary_command", 
        ""
    )
    
    # Stats command
    weechat.hook_command(
        "sumstats",
        "Show history statistics for current buffer",
        "",
        "Show number of stored lines, timestamps, and other history info",
        "",
        "stats_command",
        ""
    )
    
    # Clean command
    weechat.hook_command(
        "sumclean",
        "Clean history for buffer(s)",
        "[all|buffer_name]",
        "all: clean all buffers\nbuffer_name: clean specific buffer\nno argument: clean current buffer",
        "all",
        "clean_command",
        ""
    )
    
    weechat.prnt("", "LLM Summarizer loaded! Commands:")
    weechat.prnt("", "  /sum [5m|5h|5] - Generate summary")
    weechat.prnt("", "  /sumstats - Show history statistics")
    weechat.prnt("", "  /sumclean [all] - Clean history")
# WeeChat LLM Summarizer

A Python script for WeeChat that summarizes chat conversations using local LLMs via Ollama. Get AI-powered summaries of your IRC channels without sending data to external services.

![Demo](https://img.shields.io/badge/Works%20With-Ollama-orange)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![WeeChat](https://img.shields.io/badge/WeeChat-2.7+-green)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 🤖 **Local AI** - Uses Ollama with your choice of models (llama, gemma, mistral, etc.)
- 🔒 **Privacy First** - All processing happens locally, no data sent to the cloud
- ⚡ **Lightweight** - No external dependencies, uses only Python standard library
- 🎨 **Clean Output** - Green-colored summaries with proper spacing
- ⚙️ **Configurable** - Customizable history size, model settings, and prompts
- 🔄 **Real-time** - Summarizes current channel conversation history
- 📝 **Customizable Prompts** - External prompt files for easy customization

## 🚀 Quick Start

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (recommended for speed)
ollama pull llama3.2:3b

# Start Ollama service
ollama serve
```

### 2. Install the Script

```bash
# Navigate to WeeChat python directory (common locations)
cd ~/.local/share/weechat/python/  # macOS
# cd ~/.weechat/python/            # Linux
# cd %APPDATA%\WeeChat\python\     # Windows

# Download the script and prompt template
wget https://codeberg.org/anton-doltan/weechat-llm-summarizer/raw/branch/main/llm_summarizer.py
wget https://codeberg.org/anton-doltan/weechat-llm-summarizer/raw/branch/main/summary_prompt.txt
```

### 3. Load in WeeChat

```bash
/python load llm_summarizer.py
```

### 4. Start Using It!

```bash
# Generate summary in current buffer
/sum
```

### LLM & Behavior Configuration

```bash
/set plugins.var.python.llm_summarizer.llm_url "http://localhost:11434/api/generate"
/set plugins.var.python.llm_summarizer.llm_model "llama3.2:3b"
/set plugins.var.python.llm_summarizer.temperature "0.7"
/set plugins.var.python.llm_summarizer.max_history_lines "50"
/set plugins.var.python.llm_summarizer.prompt_file "summary_prompt.txt"
```
###  History Statistics 
```bash
/sumstats # Displays global stats

/sumclean  # Clean current buffer history

/sumclean all # Clean all buffers history

/sumclean channel # Clean specific buffer by name
```
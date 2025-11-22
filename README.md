# WeeChat LLM Summarizer

A Python script for WeeChat that summarizes chat conversations using local LLMs via Ollama. Get AI-powered summaries of your IRC channels without sending data to external services.

![Demo](https://img.shields.io/badge/Works%20With-Ollama-orange)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![WeeChat](https://img.shields.io/badge/WeeChat-2.7+-green)

## ✨ Features

- 🤖 **Local AI** - Uses Ollama with your choice of models (llama, gemma, mistral, etc.)
- 🔒 **Privacy First** - All processing happens locally, no data sent to the cloud
- ⚡ **Lightweight** - No external dependencies, uses only Python standard library
- 🎨 **Clean Output** - Green-colored summaries with proper spacing
- ⚙️ **Configurable** - Customizable triggers, history size, and model settings
- 🔄 **Real-time** - Summarizes current channel conversation history

## 🚀 Quick Start

### 1. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (recommended for speed)
ollama pull llama3.2:3b

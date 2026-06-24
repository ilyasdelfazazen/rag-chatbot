# RAG Chatbot

A web-based chatbot built with Flask that supports both standard LLM chat and Retrieval-Augmented Generation (RAG) over uploaded documents. Powered by Groq's inference API and LangChain.

## Features

- Chat with multiple LLMs via Groq (Llama 3, Llama 4, DeepSeek, Gemma 2)
- Upload PDF or TXT documents and query them using RAG
- Multilingual embeddings (`paraphrase-multilingual-mpnet-base-v2`)
- Vector storage with ChromaDB (persisted locally)
- GPU acceleration via PyTorch (falls back to CPU automatically)
- Toggle between standard chat and RAG mode per message

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask |
| LLM API | Groq |
| RAG Pipeline | LangChain + ChromaDB |
| Embeddings | HuggingFace Sentence Transformers |
| Frontend | Vanilla JS + CSS |

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ilyasdelfazazen/rag-chatbot.git
cd rag-chatbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free API key at [console.groq.com](https://console.groq.com).

### 4. Run the app

```bash
python app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

## Usage

1. **Standard chat** — type a message and hit Send
2. **RAG mode** — upload a PDF or TXT file, check the "Use RAG" toggle, then ask questions about the document
3. **Switch models** — use the model dropdown to choose the LLM

## Project Structure

```
rag-chatbot/
├── app.py               # Flask app, RAG pipeline, Groq API calls
├── requirements.txt
├── .env                 # API key (not committed)
├── static/
│   ├── script.js        # Frontend logic
│   └── style.css
└── templates/
    └── index.html       # Chat UI
```

## Available Models

- Llama 3.3 70B
- Llama 3 70B / 8B
- Llama 4 Scout 17B
- DeepSeek R1 Distill Llama 70B
- Gemma 2 Instruct

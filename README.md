# 🤖 Smart Document Assistant (RAG)

An enterprise-grade Retrieval-Augmented Generation (RAG) application built with Streamlit, LangChain, and Google Gemini. This assistant allows users to upload lengthy PDF documents and chat with them in a highly interactive, context-aware interface.

## ✨ Key Features

*   **Progressive UI & Focus Mode:** Step-by-step document ingestion that hides the upload interface once the database is ready, ensuring a distraction-free chat experience.
*   **ChatGPT-Style Conversational Interface:** Persistent chat history with visual message containers and isolated context memory.
*   **Bring Your Own Key (BYOK):** Secure API key management allowing users to use the app's default key or provide their own Google API key. *(Note: Currently powered by Gemini, with support for other major APIs coming soon).*
*   **Ghost Bug Prevention:** Utilizes UUIDs for dynamic ChromaDB collection generation, preventing chunk duplication and memory leaks across sessions.
*   **Source Transparency:** Every AI response includes an expandable "Search References" section, displaying the exact text chunks used to generate the answer.

## 🛠️ Tech Stack

*   **Frontend:** Streamlit
*   **LLM & Orchestration:** LangChain, Google Gemini (`gemini-flash-latest`)
*   **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)
*   **Vector Database:** ChromaDB
*   **Document Processing:** PyPDF, RecursiveCharacterTextSplitter

## 🚀 How to Run Locally

1. Clone this repository:
   ```bash
   git clone [https://github.com/TheAkbarifard/rag-assistant.git](https://github.com/TheAkbarifard/rag-assistant.git)
   cd rag-assistant
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

## 🐳 Docker Support
This project is fully dockerized for platform-agnostic deployment. *(See Dockerfile for build instructions).*

## 🔮 Future Roadmap
*   **Multi-Provider API Support:** Expand BYOK capabilities to support other popular LLMs (e.g., OpenAI, Anthropic).
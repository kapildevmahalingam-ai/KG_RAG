# Tamil Nadu Agriculture Schemes — Knowledge Graph RAG (KG-RAG)

An intelligent, multi-PDF Retrieval-Augmented Generation (RAG) assistant backed by a **Neo4j Aura DB** Knowledge Graph and **NetworkX** traversal. It features a **FastAPI** backend and a ChatGPT-style **Streamlit** frontend with model version switching and persistent chat history.

## Project Layout

```text
W3_LLM_KG_RAG/
├── Data/                   # Place your scheme PDFs here
├── faiss_index/            # Optional vector fallback cache
├── guardrails.py           # Safety & domain relevance guardrails
├── kg_builder.py           # Extracts entities/relations & populates Neo4j & NetworkX
├── rag.py                  # KG graph querying & Gemini answer generation
├── api.py                  # FastAPI backend server
├── app.py                  # Streamlit ChatGPT-style frontend UI
├── eval_deepeval.py        # DeepEval evaluation pipeline
├── requirements.txt
├── .env                    # Configuration credentials
└── chats.json              # Chat session history storage

Tech Stack & Architecture
Knowledge Graph: Neo4j Aura DB & NetworkX (in-memory graph traversal).

LLM & Embeddings: Google Gemini (gemini-3.5-flash, etc.).

Backend: FastAPI (with asynchronous endpoints & streaming responses).

Frontend: Streamlit (ChatGPT-style interface with chat management and model switcher).

Guardrails & Evals: Rule-based input filtering and DeepEval testing metrics.

Setup & Installation
Clone the repository and navigate into the project folder:

PowerShell
cd W3_LLM_KG_RAG
Create and activate a Python virtual environment:

PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
Install dependencies:

PowerShell
pip install -r requirements.txt
Configure your environment variables. Create a .env file in the root directory:

Code snippet
GEMINI_API_KEY="your-google-ai-studio-api-key"
DEFAULT_CHAT_MODEL="gemini-3.5-flash"
NEO4J_URI="bolt+s://your-instance-id.databases.neo4j.io"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="your-neo4j-password"
Building the Knowledge Graph
Place your official Tamil Nadu agriculture scheme PDFs inside the Data/ folder, then run the builder script to parse entities, relationships, and benefits into Neo4j:

PowerShell
python kg_builder.py
Running the Application
Terminal 1 — Start the FastAPI Backend
PowerShell
uvicorn api:app --reload --port 8000
API documentation available at http://127.0.0.1:8000/docs.

Terminal 2 — Start the Streamlit Frontend
PowerShell
streamlit run app.py
Evaluation
Run the DeepEval evaluation suite to test answer relevancy and faithfulness against the Knowledge Graph context:

PowerShell
python eval_deepeval.py
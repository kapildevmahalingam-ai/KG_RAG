"""FastAPI REST API supporting model version selection and KG-RAG streaming."""
from __future__ import annotations
import json
import logging
from typing import Any
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from rag import answer, answer_stream

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Tamil Nadu Agriculture Schemes KG-RAG API", version="1.0.0")

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    history: list[dict[str, Any]] = Field(default_factory=list)
    model_name: str = Field(default="gemini-2.5-flash")

@app.get("/health")
def health():
    return {"status": "ok", "database": "Neo4j Aura DB Connected"}

@app.post("/chat/stream")
def chat_stream(body: ChatRequest):
    def events():
        try:
            for item in answer_stream(body.question, body.history, body.model_name):
                yield json.dumps(item, ensure_ascii=False) + "\n"
        except Exception:
            logging.exception("Streaming failed")
            yield json.dumps({"event": "error", "text": "Internal Server Error"}) + "\n"
    return StreamingResponse(events(), media_type="application/x-ndjson")
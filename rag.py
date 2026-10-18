"""Retrieval from Neo4j/NetworkX Knowledge Graph and grounded answer generation."""
from __future__ import annotations
import os
from typing import Iterator
from neo4j import GraphDatabase
import networkx as nx
from dotenv import load_dotenv
from google import genai
from google.genai import types
from guardrails import check_input, check_output

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_driver = None
_nx_graph = None

def get_db_connection():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _driver

def query_knowledge_graph(question: str) -> tuple[str, list[dict]]:
    driver = get_db_connection()
    context_parts = []
    sources = []
    
    # Query Neo4j Aura DB for schemes, benefits, and eligibility matching query terms
    with driver.session() as session:
        result = session.run(
            """
            MATCH (s:Scheme)-[:PROVIDES_BENEFIT]->(b:Benefit)
            OPTIONAL MATCH (s)-[:HAS_ELIGIBILITY]->(e:Eligibility)
            RETURN s.name AS scheme, b.description AS benefit, e.description AS eligibility, s.source AS source, s.page AS page
            LIMIT 15
            """
        )
        for record in result:
            scheme = record["scheme"]
            benefit = record["benefit"]
            eligibility = record["eligibility"] or "Not specified"
            source = record["source"]
            page = record["page"]

            context_parts.append(f"Scheme: {scheme}\nBenefit: {benefit}\nEligibility: {eligibility}\nSource: {source} (Page {page})")
            sources.append({"pdf": source, "page": page})

    return "\n\n".join(context_parts), sources

def answer(question: str, history: list[dict] | None = None, model_name: str = "gemini-2.5-flash") -> dict:
    ok, reason = check_input(question)
    if not ok:
        return {"answer": reason, "sources": []}
    
    context_text, sources = query_knowledge_graph(question)
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    You are the Tamil Nadu Agriculture Schemes Assistant powered by a Knowledge Graph.
    Answer the user question using ONLY the Knowledge Graph context provided below.
    Cite factual claims inline with [Filename, page N]. If unavailable, state you couldn't find it.

    Knowledge Graph Context:
    {context_text}

    User Question: {question}
    """

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2)
    )
    
    text = response.text or ""
    valid, safe_text = check_output(text)
    if not valid:
        text = safe_text

    return {"answer": text, "sources": sources}

def answer_stream(question: str, history: list[dict] | None = None, model_name: str = "gemini-2.5-flash") -> Iterator[dict]:
    try:
        ok, reason = check_input(question)
        if not ok:
            yield {"event": "replace", "text": reason}
            yield {"event": "sources", "sources": []}
            return

        context_text, sources = query_knowledge_graph(question)
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
        You are the Tamil Nadu Agriculture Schemes Assistant powered by a Knowledge Graph.
        Answer the user question using ONLY the Knowledge Graph context provided below.
        Cite factual claims inline with [Filename, page N].

        Knowledge Graph Context:
        {context_text}

        User Question: {question}
        """

        stream = client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2)
        )
        
        parts = []
        for chunk in stream:
            delta = chunk.text if chunk and hasattr(chunk, "text") else ""
            if delta:
                parts.append(delta)
                yield {"event": "token", "text": delta}

        full_text = "".join(parts)
        valid, safe_text = check_output(full_text)
        if not valid:
            yield {"event": "replace", "text": safe_text}

        yield {"event": "sources", "sources": sources}

    except Exception as exc:
        yield {"event": "replace", "text": f"Error during generation: {str(exc)}"}
        yield {"event": "sources", "sources": []}
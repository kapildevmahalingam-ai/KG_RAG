"""Extracts PDFs in micro-batches, maps entities/relations, 
and stores them into Neo4j Aura DB and NetworkX.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import pymupdf
import networkx as nx
from neo4j import GraphDatabase
from dotenv import load_dotenv
from google import genai

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-3.8-flash"

def extract_pdf_pages(pdf_path: Path) -> list[dict]:
    pages = []
    with pymupdf.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text", sort=True).strip()
            if text:
                pages.append({"text": text, "source": pdf_path.name, "page": page_number})
    return pages

def extract_kg_from_text(client: genai.Client, text: str, source: str, page: int) -> dict:
    prompt = f"""
    Analyze the following agriculture document text from '{source}' (Page {page}). 
    Extract a Knowledge Graph containing:
    1. 'Schemes' (Name of the government scheme)
    2. 'Benefits' (Subsidies, financial help, or support offered)
    3. 'Eligibility' (Who can apply)
    
    Return valid JSON format strictly like this:
    {{
      "schemes": [
        {{"name": "Scheme Name", "benefits": "Benefit description", "eligibility": "Eligibility criteria"}}
      ]
    }}
    Text: {text[:3000]}
    """
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        cleaned = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        return {"schemes": []}

def main():
    if not DATA_DIR.exists():
        raise SystemExit(f"Data directory missing: {DATA_DIR}")
    
    pdf_files = sorted(DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        raise SystemExit(f"No PDF files found in {DATA_DIR}")

    client = genai.Client(api_key=GEMINI_API_KEY)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    nx_graph = nx.DiGraph()

    print("Connecting to Neo4j Aura DB & building Knowledge Graph...")
    with driver.session() as session:
        # Clear existing graph schema if needed
        session.run("MATCH (n) DETACH DELETE n")

        for pdf_path in pdf_files:
            print(f"Processing: {pdf_path.name}")
            pages = extract_pdf_pages(pdf_path)
            
            for page_data in pages:
                # Micro-batch extraction per page
                kg_data = extract_kg_from_text(client, page_data["text"], page_data["source"], page_data["page"])
                
                for item in kg_data.get("schemes", []):
                    s_name = item.get("name", "Unknown Scheme")
                    benefit = item.get("benefits", "N/A")
                    elig = item.get("eligibility", "N/A")
                    source = page_data["source"]
                    page = page_data["page"]

                    # Add to NetworkX
                    nx_graph.add_node(s_name, type="Scheme", source=source, page=page)
                    nx_graph.add_node(benefit, type="Benefit")
                    nx_graph.add_edge(s_name, benefit, relation="PROVIDES_BENEFIT")

                    # Add to Neo4j Aura DB
                    session.run(
                        """
                        MERGE (s:Scheme {name: $s_name})
                        SET s.source = $source, s.page = $page
                        MERGE (b:Benefit {description: $benefit})
                        MERGE (e:Eligibility {description: $elig})
                        MERGE (s)-[:PROVIDES_BENEFIT]->(b)
                        MERGE (s)-[:HAS_ELIGIBILITY]->(e)
                        """,
                        s_name=s_name, benefit=benefit, elig=elig, source=source, page=page
                    )

    driver.close()
    print("Knowledge Graph construction completed in Neo4j Aura DB & NetworkX!")

if __name__ == "__main__":
    main()
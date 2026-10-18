import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to: {uri}")
try:
  driver = GraphDatabase.driver(uri, auth=(user, password))
  driver.verify_connectivity()
  print("SUCCESS: Connected to Neo4j Aura DB successfully!")
  driver.close()
except Exception as e:
  print(f"FAILED: {e}")
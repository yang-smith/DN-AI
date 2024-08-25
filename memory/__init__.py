import os
import memory.db
import memory.vector_db
import memory.sessions
import networkx as nx

entities_db = memory.vector_db.VectorDB(db_path='./chroma_entities')
docs_DB = memory.db.DB()
base_sessions = memory.sessions.Sessions()
file_path = "./graphtest.graphml"
if os.path.exists(file_path):
    base_graph = nx.read_graphml(file_path)
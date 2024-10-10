import walnut.memory.graph_extractor as graph_extractor
from walnut.memory.pre_load_md import pre_load_md
from walnut.memory.db import DB
import asyncio
import os
import networkx as nx
import pytest

pytestmark = pytest.mark.asyncio

def test_add_nodes():
    dir_path = './testDB'

    folder_path = 'docs/gongzhonghao'
    documents = pre_load_md(folder_path)

    db = DB(sqlitedb_path=f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
    db.insert_documents(documents)
    # docs = db.get_documents(documents)

    # extractor = graph_extractor.GraphExtractor()
    # asyncio.run(extractor.extract_graph(docs, file_path=f"{dir_path}/records.graphml"))

    # file_path = f"{dir_path}/records.graphml"
    # if os.path.exists(file_path):
    #     graph = nx.read_graphml(file_path)
    #     extractor.set_entities_db(graph, f"{dir_path}/entities")
    
    # asyncio.run(extractor.summarize_graph_descriptions(file_path, 300))

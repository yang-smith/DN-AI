from FlagEmbedding import FlagReranker
import pytest
import tempfile
import os
from walnut.memory.db import DB
from walnut.memory.query import find_related_entities
from walnut.memory.vector_db import VectorDB
import networkx as nx
import time

reranker = FlagReranker( "BAAI/bge-reranker-base")
# reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation
pytestmark = pytest.mark.asyncio

async def test_rerank():
    dir_path = './testDB'
    db = DB(sqlitedb_path = f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
    entities_db = VectorDB(db_path=f"{dir_path}/entities")
    graph = nx.read_graphml(f"{dir_path}/records.graphml")

    query_content = "最近有什么接龙活动？"
    start_date = "2024-08-01"
    end_date = "2024-08-31"

    
    info = await find_related_entities(query=query_content, vecdb=entities_db, graph=graph)
    docs = db.query_by_time(start_date, end_date, query_content, threshold=300)

    start_time = time.time()
    # 准备查询和文档对（docs）
    query_doc_pairs_docs = [[query_content, doc] for doc in docs['documents'][0]]

    # 准备查询和文档对（info）
    query_doc_pairs_info = [[query_content, item.split(': ', 1)[1]] for item in info if ': ' in item]

    # 计算分数（docs）
    scores_docs = reranker.compute_score(query_doc_pairs_docs, normalize=True)

    # 计算分数（info）
    scores_info = reranker.compute_score(query_doc_pairs_info, normalize=True)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nTotal execution time: {total_time:.2f} seconds")

    # 显示每个文档的分数（docs）
    print("Scores for docs:")
    for doc, score in zip(docs['documents'][0], scores_docs):
        print(f"Document: {doc[:50]}...")  # 只显示文档的前50个字符
        print(f"Score: {score}")
        print("---")

    # 显示每个文档的分数（info）
    print("\nScores for info:")
    for item, score in zip(query_doc_pairs_info, scores_info):
        print(f"Document: {item[1][:50]}...")  # 只显示文档的前50个字符
        print(f"Score: {score}")
        print("---")
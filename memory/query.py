
from datetime import datetime
import os
import memory.vector_db
import asyncio
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from lib.ai import truncate_list_by_token_size
import lib.ai
from memory.prompt.prompt import prompt_memory 
import networkx as nx



async def query(id, user_input, graph, model='gpt-4o-2024-08-06'):

    if user_input == "exit":
        return

    time_start = datetime.now()  

    vecdb = memory.entities_db
    info = await find_related_entities(query=user_input,vecdb=vecdb, graph=graph)
    print(info)

    db = memory.docs_DB
    docs = db.query(user_input)
    contents = ''
    for content in docs['documents'][0]:
        contents += content
    print(docs)
    # print(contents)

    time_end = datetime.now() 
    print(f"{round((time_end - time_start).total_seconds(), 2)}s") 

    time_start = datetime.now()  
    messages = memory.base_sessions.get_messages(id)
    prompt = prompt_memory.format(user_input=user_input,memory_graph=info, memory_chunk=contents)
    messages.append({"role": "user",
            "content": prompt,})
    message = {
            "role": "user",
            "content": user_input,
        }
    memory.base_sessions.add_message(id, message)
    print(messages)
    results = lib.ai.ai_long_chat(messages,model)
    print('AI： \n '+ results)
    message = {
        "role": "assistant",
        "content": results,
    }
    memory.base_sessions.add_message(id, message)
    time_end = datetime.now() 
    print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    
    
    
    return results

async def find_related_entities(
    query: str,
    vecdb,
    graph,
    max_entities: int = 30,
    max_token_size: int = 3000
):
    # 从Chroma DB中查找相关实体
    entities = vecdb.query_entities(query, n_results=max_entities)
    
    async def get_entity_edges(graph: nx.Graph, entity: str):
        return await asyncio.to_thread(list, graph.edges(entity, data=True))
    
    # 获取实体相关的边
    edges = await asyncio.gather(*[get_entity_edges(graph, entity) for entity in entities])
    
    # 收集一跳节点
    one_hop_nodes = set()
    for edge_list in edges:
        one_hop_nodes.update([e[1] for e in edge_list])
    
    # print(one_hop_nodes)

    # 收集所有相关的节点和边的描述
    descriptions = []
    
    # 添加节点描述
    for entity in entities:
        node_data = graph.nodes[entity]
        if 'description' in node_data:
            descriptions.append(f" \n '{entity}': {node_data['description']}")
    
    # 添加边描述并按权重排序
    edge_descriptions = []
    for edge_list in edges:
        for edge in edge_list:
            source, target, data = edge
            if 'description' in data and 'weight' in data:
                edge_descriptions.append((
                    f"边 '{source}' 到 '{target}': {data['description']}",
                    data['weight']
                ))
    
    edge_descriptions.sort(key=lambda x: x[1], reverse=True)
    descriptions.extend([desc for desc, _ in edge_descriptions])
    
    # print(edge_descriptions)
    # print(descriptions)

    descriptions = truncate_list_by_token_size(descriptions, max_token_size)
    
    return descriptions

async def find_related_edges_from_graph(
    entities: List[str],
    graph_storage,
    max_edges: int = 100,
    max_token_size: int = 1000
):
    # 获取所有相关边
    all_edges = set()
    for entity in entities:
        edges = await graph_storage.get_node_edges(entity)
        all_edges.update([tuple(sorted(e)) for e in edges])
    
    # 获取边的数据和度
    edge_data = await asyncio.gather(*[graph_storage.get_edge(e[0], e[1]) for e in all_edges])
    edge_degrees = await asyncio.gather(*[graph_storage.edge_degree(e[0], e[1]) for e in all_edges])
    
    # 构建边信息
    edge_info = []
    for edge, data, degree in zip(all_edges, edge_data, edge_degrees):
        if data:
            edge_info.append({
                "source": edge[0],
                "target": edge[1],
                "data": data,
                "degree": degree
            })
    
    # 按度和权重排序
    edge_info.sort(key=lambda x: (x["degree"], x["data"].get("weight", 0)), reverse=True)
    
    # 截断到指定数量和token大小
    edge_info = edge_info[:max_edges]
    edge_info = truncate_list_by_token_size(edge_info, max_token_size)
    
    return edge_info



async def ask(graph, vecdb):

    while 1:
        user_input = input("问点什么：")
        if user_input == "exit":
            break

        time_start = datetime.now()  
        info = await find_related_entities(query=user_input,vecdb=vecdb, graph=graph)
        print(info)

        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    
        time_start = datetime.now()  
        prompt = prompt_memory.format(user_input=user_input,memory=info)
        # results = lib.ai.ai_chat(prompt,'gpt-4o-mini')
        # print('4o-mini '+ results)
        # results = lib.ai.ai_chat(prompt,'gpt-4o-2024-08-06')
        # print('gpt-4o-2024-08-06 \n '+ results)
        results = lib.ai.ai_chat(prompt,'gemini-1.5-pro')
        print('gemini-1.5-pro \n '+ results)
        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    

async def main():

    file_path = "./graphtest.graphml"
    if os.path.exists(file_path):
        try:
            results = nx.read_graphml(file_path)
            print(f"成功读取图形文件：{file_path}")
            # node_ids = list(results.nodes())
            # print(node_ids)
            db = memory.vector_db.VectorDB(db_path='./chroma_entities')
            # db.upsert_entities(node_ids)
            await ask(results,db)
            # print(db.query_entities('有啥好吃的'))
            # info = await find_related_entities(query='有啥好吃的',vecdb=db, graph=results)
            # print(info)
        except Exception as e:
            print(f"error：{e}")
    else:
        print(f"文件 {file_path} 不存在")



if __name__ == '__main__':

    asyncio.run(main())


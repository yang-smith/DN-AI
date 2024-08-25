from datetime import datetime
import os
import networkx as nx
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt

import memory.prompt.prompt_communities

def nx_to_igraph(nx_graph):
    """将 NetworkX 图转换为 igraph 图"""
    # 创建 igraph 图
    ig_graph = ig.Graph()
 
    ig_graph.add_vertices(list(nx_graph.nodes()))
    ig_graph.add_edges(list(nx_graph.edges()))
    
    # 复制节点属性
    node_attrs = set().union(*(d.keys() for n, d in nx_graph.nodes(data=True)))
    for attr in node_attrs:
        ig_graph.vs[attr] = [nx_graph.nodes[node].get(attr) for node in nx_graph.nodes()]
    
    # 复制边属性
    edge_attrs = set().union(*(d.keys() for u, v, d in nx_graph.edges(data=True)))
    for attr in edge_attrs:
        ig_graph.es[attr] = [nx_graph.edges[edge].get(attr) for edge in nx_graph.edges()]
    
    return ig_graph

def apply_leiden_clustering(nx_graph):
    """对 NetworkX 图应用 Leiden 聚类算法"""
    # 确保图是连通的
    if not nx.is_connected(nx_graph):
        largest_cc = max(nx.connected_components(nx_graph), key=len)
        nx_graph = nx_graph.subgraph(largest_cc).copy()
        print("警告：原图不是连通的。只使用最大连通分量进行聚类。")
    
    # 移除自环
    nx_graph.remove_edges_from(nx.selfloop_edges(nx_graph))
    
    # 转换为 igraph 图
    ig_graph = nx_to_igraph(nx_graph)
    
    # 应用 Leiden 算法
    partition = la.find_partition(ig_graph, la.ModularityVertexPartition)
    
    # 将聚类结果添加回 NetworkX 图
    for i, community in enumerate(partition):
        for node in community:
            nx_graph.nodes[ig_graph.vs[node]['name']]['community'] = i
    
    return nx_graph, partition

def visualize_communities(graph):
    pos = nx.spring_layout(graph)
    communities = set(nx.get_node_attributes(graph, 'community').values())
    color_map = plt.cm.get_cmap('viridis', len(communities))
    
    plt.figure(figsize=(12, 8))
    for i, com in enumerate(communities):
        node_list = [node for node in graph.nodes() if graph.nodes[node]['community'] == com]
        nx.draw_networkx_nodes(graph, pos, node_list, node_color=[color_map(i)], node_size=100)
    
    nx.draw_networkx_edges(graph, pos, alpha=0.5)
    plt.title("Community Structure")
    plt.axis('off')
    plt.show()

def get_community_info(graph, community_id):
    """获取指定社区的节点和边信息"""
    nodes = [node for node, data in graph.nodes(data=True) if data.get('community') == community_id]
    subgraph = graph.subgraph(nodes)
    
    # 构建实体信息
    entities = "Entities\nid,entity,description\n"
    for node_id, data in subgraph.nodes(data=True):
        description = data.get('description', '')
        entities += f"{node_id},   {description}\n"
    
    # 构建关系信息
    relationships = "\nRelationships\nid,source,target,description\n"
    for source, target, data in subgraph.edges(data=True):
        description = data.get('description', '')  # 使用'd5'作为描述
        relationships += f"{source}->{target}:   {description}\n"
    
    return entities + relationships

def print_all_communities_info(graph):
    """打印所有社区的信息"""
    import memory.prompt.prompt_communities 
    import lib.ai
    communities = set(nx.get_node_attributes(graph, 'community').values())
    i = 0
    for community_id in communities:
        print(f"\n--- Community {community_id} ---\n")
        info = get_community_info(graph, community_id)
        print(info)
        prompt = memory.prompt.prompt_communities.COMMUNITY_REPORT_PROMPT.format(input_text = info)
        # print(prompt)
        result1 = lib.ai.ai_chat(prompt,"gpt-4o-mini")
        print('gpt4o'+result1)
        result2 = lib.ai.ai_chat(prompt,"gemini-1.5-flash")
        print('gemini'+result2)
        result3 = lib.ai.ai_chat(prompt,"claude-3-haiku-20240307")
        print('claude'+result3)
        i+=1
        if i > 2:
            break

import memory.vector_db
import asyncio
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from lib.ai import truncate_list_by_token_size

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
    import lib.ai
    from memory.prompt.prompt import prompt_memory
    from memory.query import query 

    while 1:
        user_input = input("问点什么：")
        if user_input == "exit":
            break

        results =await query('0',user_input,graph, model='gpt-4o-2024-08-06')
        # time_start = datetime.now()  
        # info = await find_related_entities(query=user_input,vecdb=vecdb, graph=graph)
        # print(info)

        # time_end = datetime.now() 
        # print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    
        # time_start = datetime.now()  
        # prompt = prompt_memory.format(user_input=user_input,memory=info)
        # # results = lib.ai.ai_chat(prompt,'gpt-4o-mini')
        # # print('4o-mini '+ results)
        # # results = lib.ai.ai_chat(prompt,'gpt-4o-2024-08-06')
        # # print('gpt-4o-2024-08-06 \n '+ results)
        # results = lib.ai.ai_chat(prompt,'gemini-1.5-pro')
        # print('gemini-1.5-pro \n '+ results)
        # time_end = datetime.now() 
        # print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    

async def main():

    file_path = "./graphtest.graphml"
    if os.path.exists(file_path):
        try:
            results = nx.read_graphml(file_path)
            print(f"成功读取图形文件：{file_path}")
            # node_ids = list(results.nodes())
            # print(node_ids)
            db = memory.entities_db
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

    # # 假设 'results' 是您之前得到的 NetworkX 图
    # clustered_graph, partition = apply_leiden_clustering(results)

    # # 打印一些聚类结果
    # print(f"发现的社区数量: {len(partition)}")
    # print(f"模块度: {partition.quality()}")

    # # 您可以遍历节点查看它们的社区分配
    # for node in clustered_graph.nodes(data=True):
    #     print(f"节点 {node[0]} 属于社区 {node[1]['community']}")

    # visualize_communities(clustered_graph)
    # print_all_communities_info(clustered_graph)
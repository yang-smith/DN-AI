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
test_input = """
Entities
id,entity,description
身份证信息,   身份证信息是入住者必须登记的有效身份证明，包括随行人员和临时入住者
湖州市,   湖州市是浙江省的一个城市，DN余村位于该城市的安吉县  
床品三件套,   床品三件套是指使用过的床上用品，需拆卸并清洗后放回柜子
退房流程,   退房流程是指在离开住宿时需要遵循的步骤和注意事项  
PASSWORD,   The password for the Wi-Fi is 88888888
管理人员,   管理人员是指负责管理住宿的工作人员，客人需将房卡钥匙归还给他们
管理人员负责监督入住者的行为和管理住宿环境，入住者需与其说明情况
房卡,   房卡可用作在地各合作商家的优惠凭证，并在退房时需归还  
安吉数字游民公社（DNA）,   安吉数字游民公社（DNA）是DN余村之前的数字游民公社，提供类似的服务
安吉县,   安吉县是浙江省的一个县，余村位于该县的天荒坪镇      
安吉县是湖州市下辖的一个县，DN余村位于该县的天荒坪镇
两山景区,   两山景区是以“两山”实践为主题的生态旅游和乡村度假景区，位于余村
房间与床位,   房间与床位是入住者使用的住宿设施，不能私下转让或调换
个人物品,   个人物品是指客人在房间内的私有物品，需在退房前清理
DN余村是一个数字游民公社，提供工作和生活的综合园区，强调开放、共建、共享的价值观
DN余村是一个提供住宿的地方，要求入住者遵守特定的入住指南和规定
“DN余村”是“Digital Nomad 余村”的缩写，位于浙江省湖州市安吉县天荒坪镇，是一个数字游民公社
“DN余村”是一个开放的宠物友好社区，提供多种房型选择，包括4人间 、6人间、单人间、双人标准间和家庭房。
DN余村是一个距离天荒坪镇政府步行10分钟的地方。
WI-FI,   “DN余村”提供Wi-Fi服务，名称为DN_2.4和DN_5G，密码为88888888。
客服,   客服负责处理退房相关事宜，并提供帮助和信息
客服负责协调房间和处理入住者的特殊请求。
客服是负责处理入住者问题和安排的人员，入住者需要与其沟通相关事宜
客服是指提供帮助和支持的工作人员，客人需与其沟通退房事宜      
客服负责接收和处理社区内的反馈和报修请求
门禁系统,   入住后，客服会通过微信推送门禁系统的相关信息。    
管理员,   管理员负责管理退房流程，并协助客人完成退房
管理员负责处理社区内的安全问题和反馈
公共空间,   社区内的公共空间需保持良好状态，出现损坏需及时反馈
续订房间,   续订房间是入住者在入住后继续使用房间的请求，需要提前告知客服
垃圾,   垃圾是指在房间内产生的废弃物，需在退房前清理

Relationships
id,source,target,description
身份证信息->DN余村:   入住者必须登记身份证信息以符合入住要求  
湖州市->DN余村:   DN余村位于湖州市安吉县天荒坪镇
床品三件套->退房流程:   退房流程要求拆卸床品三件套并清洗后放回柜子
退房流程->客服:   退房流程中客人需与客服沟通处理退房事宜      
退房流程->个人物品:   退房流程要求客人在退房前清理房间内的个人物品
退房流程->垃圾:   退房流程要求客人在退房前清理房间内的垃圾    
退房流程->管理人员:   退房流程中客人需将房卡钥匙归还给管理人员
PASSWORD->WI-FI:   The Wi-Fi requires the password 88888888 for access
管理人员->DN余村:   管理人员负责监督入住者并处理相关问题      
房卡->客服:   房卡在退房时需归还给客服
安吉数字游民公社（DNA）->DN余村:   DN余村是安吉数字游民公社（DNA）之后建立的第二个数字游民公社
安吉县->DN余村:   DN余村位于安吉县的天荒坪镇
DN余村位于安吉县内
房间与床位->DN余村:   房间与床位是DN余村提供的住宿设施，入住者需遵守使用规定
浙江省->DN余村:   DN余村位于浙江省内
DN余村位于浙江省湖州市安吉县天荒坪镇
DN余村->客服:   客服在“DN余村”中负责协调房间和处理入住者的特殊请求。
入住者需要与客服沟通以处理入住相关事宜
DN余村->WI-FI:   “DN余村”提供Wi-Fi服务，供入住者使用。        
DN余村->门禁系统:   门禁系统在“DN余村”中用于管理入住者的出入。
DN余村->续订房间:   入住者需提前告知客服以续订房间，确保安排顺利
客服->管理员:   客服和管理员共同负责处理退房事宜
管理员和客服共同负责处理社区内的安全和反馈问题
客服->公共空间:   公共空间的损坏需及时反馈给客服进行报修 """

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
        # result2 = lib.ai.ai_chat(prompt,"gemini-1.5-pro")
        # print('gemini'+result2)
        # result3 = lib.ai.ai_chat(prompt,"claude-3-5-sonnet-20240620")
        # print('claude'+result3)
        # break
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

    # file_path = "./graphtest.graphml"
    # if os.path.exists(file_path):
    #     results = nx.read_graphml(file_path)
    #     print(f"成功读取图形文件：{file_path}")
    #     # 假设 'results' 是您之前得到的 NetworkX 图
    #     clustered_graph, partition = apply_leiden_clustering(results)

    #     # 打印一些聚类结果
    #     print(f"发现的社区数量: {len(partition)}")
    #     print(f"模块度: {partition.quality()}")

    #     # 您可以遍历节点查看它们的社区分配
    #     # for node in clustered_graph.nodes(data=True):
    #     #     print(f"节点 {node[0]} 属于社区 {node[1]['community']}")

    #     # visualize_communities(clustered_graph)
    #     print_all_communities_info(clustered_graph)
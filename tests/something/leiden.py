import os
import networkx as nx
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt

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
    import prompt_entities
    import extract
    communities = set(nx.get_node_attributes(graph, 'community').values())
    i = 0
    for community_id in communities:
        print(f"\n--- Community {community_id} ---\n")
        info = get_community_info(graph, community_id)
        print(info)
        prompt = prompt_entities.COMMUNITY_REPORT_PROMPT.format(input_text = info)
        # print(prompt)
        result1 = extract.ai_chat(prompt,"gpt-4o-mini")
        print('gpt4o'+result1)
        result2 = extract.ai_chat(prompt,"gemini-1.5-flash")
        print('gemini'+result2)
        result3 = extract.ai_chat(prompt,"claude-3-haiku-20240307")
        print('claude'+result3)
        i+=1
        if i > 2:
            break



if __name__ == '__main__':
    file_path = "./graphtest.graphml"
    if os.path.exists(file_path):
        try:
            results = nx.read_graphml(file_path)
            print(f"成功读取图形文件：{file_path}")
            node_ids = list(results.nodes())

            print(node_ids)
            print(results.nodes['突发事件联系电话'])
        except Exception as e:
            print(f"读取图形文件时发生错误：{e}")
    else:
        print(f"文件 {file_path} 不存在")

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
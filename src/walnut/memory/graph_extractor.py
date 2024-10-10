# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""实现节点提取和构建图"""

import asyncio
import html
import logging
import numbers
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx
import tiktoken

from walnut.utils.ai import ai_chat, ai_chat_async
from walnut.memory.prompt.prompt_entities import UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT
from tqdm.asyncio import tqdm


import walnut.memory.vector_db

logging.basicConfig(filename='graph.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


DEFAULT_TUPLE_DELIMITER = "<|>"
DEFAULT_RECORD_DELIMITER = "##"
DEFAULT_COMPLETION_DELIMITER = "<|COMPLETE|>"
DEFAULT_ENTITY_TYPES = ["organization", "person", "geo", "event"]


@dataclass
class GraphExtractionResult:
    """Unipartite graph extraction result class definition."""

    output: nx.Graph
    source_docs: dict[Any, Any]

@dataclass
class Document:
    id: int
    page_content: str

class GraphExtractor:
    """Unipartite graph extractor class definition."""

    _join_descriptions: bool

    def __init__(
        self,
        join_descriptions=True,
        encoding_model: str | None = None,
    ):
        """Init method definition."""

        self._join_descriptions = join_descriptions

        encoding = tiktoken.get_encoding(encoding_model or "cl100k_base")
        yes = encoding.encode("YES")
        no = encoding.encode("NO")
        self._loop_args = {"logit_bias": {yes[0]: 100, no[0]: 100}, "max_tokens": 1}
        
        self.font_path = 'C:\\Windows\\Fonts\\simhei.ttf'  
        self.prop = fm.FontProperties(fname=self.font_path)


    async def extract_graph(self, documents, file_path = "./graphtest.graphml"):
        """从信息块转为图谱。同时保存图结构"""
        all_records: dict[int, str] = {} 
        tasks = []
        for doc in documents:
            prompt = UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT.format(doc['page_content'])
            task = ai_chat_async(prompt, model="gpt-4o-mini")  
            tasks.append((doc['id'], task))

        for i, response in enumerate(tqdm(asyncio.as_completed([task for _, task in tasks]), total=len(tasks), desc="Processing Documents")):
            doc_id = tasks[i][0]
            all_records[doc_id] = await response
            tqdm.write(f"Processed document ID {doc_id}")

        print("All documents processed.")
        
        if os.path.exists(file_path):
            try:
                graph = nx.read_graphml(file_path)
                logging.info(f"成功读取图形文件：{file_path}")
                results = await self.process_results(results=all_records, graph=graph)
            except Exception as e:
                logging.error(f"读取图形文件时发生错误：{e}")
        else:
            logging.info(f"文件 {file_path} 不存在")
            results = await self.process_results(all_records)
        
        try:
            self.visualize_and_save_graph(results, './graphtest.png', file_path)
            logging.info("图形已成功可视化并保存")
        except Exception as e:
            logging.error(f"可视化和保存图形时发生错误：{e}")
    
    async def process_results(
        self,
        results: dict[int, str],
        tuple_delimiter: str = '{tuple_delimiter}',
        record_delimiter: str = '{record_delimiter}',
        graph = None,
    ) -> nx.Graph:
        """Parse the result string to create an undirected unipartite graph.

        Args:
            - results - dict of results from the extraction chain
            - tuple_delimiter - delimiter between tuples in an output record, default is '<|>'
            - record_delimiter - delimiter between records, default is '##'
        Returns:
            - output - unipartite graph in graphML format
        """
        if graph == None:
            graph = nx.Graph()
        for source_doc_id, extracted_data in results.items():
            records = [r.strip() for r in extracted_data.split(record_delimiter)]

            for record in records:
                record = re.sub(r"^\(|\)$", "", record.strip())
                record_attributes = record.split(tuple_delimiter)

                if record_attributes[0] == '"entity"' and len(record_attributes) >= 4:
                    # add this record as a node in the G
                    entity_name = clean_str(record_attributes[1].upper())
                    entity_type = clean_str(record_attributes[2].upper())
                    entity_description = clean_str(record_attributes[3])

                    if entity_name in graph.nodes():
                        node = graph.nodes[entity_name]
                        if self._join_descriptions:
                            node["description"] = "\n".join(
                                list({
                                    *_unpack_descriptions(node),
                                    entity_description,
                                })
                            )
                        else:
                            if len(entity_description) > len(node["description"]):
                                node["description"] = entity_description
                        node["source_id"] = ", ".join(
                            list({
                                *_unpack_source_ids(node),
                                str(source_doc_id),
                            })
                        )
                        node["entity_type"] = (
                            entity_type if entity_type != "" else node["entity_type"]
                        )
                    else:
                        graph.add_node(
                            entity_name,
                            type=entity_type,
                            description=entity_description,
                            source_id=str(source_doc_id),
                        )

                if (
                    record_attributes[0] == '"relationship"'
                    and len(record_attributes) >= 5
                ):
                    # add this record as edge
                    source = clean_str(record_attributes[1].upper())
                    target = clean_str(record_attributes[2].upper())
                    edge_description = clean_str(record_attributes[3])
                    edge_source_id = clean_str(str(source_doc_id))
                    weight_str = clean_str(record_attributes[-1])
                    weight_match = re.search(r'\d+(\.\d+)?', weight_str)
                    if weight_match:
                        weight = float(weight_match.group())
                    else:
                        weight = 1.0 
                    if source not in graph.nodes():
                        graph.add_node(
                            source,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if target not in graph.nodes():
                        graph.add_node(
                            target,
                            type="",
                            description="",
                            source_id=edge_source_id,
                        )
                    if graph.has_edge(source, target):
                        edge_data = graph.get_edge_data(source, target)
                        if edge_data is not None:
                            weight += edge_data["weight"]
                            if self._join_descriptions:
                                edge_description = "\n".join(
                                    list({
                                        *_unpack_descriptions(edge_data),
                                        edge_description,
                                    })
                                )
                            edge_source_id = ", ".join(
                                list({
                                    *_unpack_source_ids(edge_data),
                                    str(source_doc_id),
                                })
                            )
                    graph.add_edge(
                        source,
                        target,
                        weight=weight,
                        description=edge_description,
                        source_id=edge_source_id,
                    )

        return graph

    def visualize_and_save_graph(self, graph: nx.Graph, file_path: str, graph_path: str):
        
        pos = nx.spring_layout(graph)  # 为图形的节点设置布局
        nx.draw(graph, pos, with_labels=False, node_color='skyblue', edge_color='#FF5733', node_size=40, font_size=5)
        
        labels = nx.draw_networkx_labels(graph, pos, font_family=self.prop.get_name(), font_size=5)
        
        plt.savefig(file_path)
        plt.close()
        nx.write_graphml(graph, graph_path)

    def set_entities_db(self, graph, db_path='./chroma_entities'):
        node_ids = list(graph.nodes())
        db = walnut.memory.vector_db.VectorDB(db_path)
        db.upsert_entities(node_ids)

    async def summarize_graph_descriptions(self, graph_path: str, threshold: int):
        """
        对图中的长描述进行总结。

        Args:
        graph_path (str): GraphML文件的路径
        threshold (int): 描述长度的阈值

        Returns:
        nx.Graph: 更新后的图
        """
        return await summarize_long_descriptions(graph_path, threshold)

def _unpack_descriptions(data: Mapping) -> list[str]:
    value = data.get("description", None)
    return [] if value is None else value.split("\n")


def _unpack_source_ids(data: Mapping) -> list[str]:
    value = data.get("source_id", None)
    return [] if value is None else value.split(", ")

def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)

async def summarize_long_descriptions(graph_path: str, threshold: int):
    """
    遍历图中所有节点，找到描述超出阈值的节点，使用AI进行总结压缩。

    Args:
    graph_path (str): GraphML文件的路径
    threshold (int): 描述长度的阈值

    Returns:
    nx.Graph: 更新后的图
    """
    # 读取图
    graph = nx.read_graphml(graph_path)

    for node, data in graph.nodes(data=True):
        description = data.get('description', '')
        if len(description) > threshold:
            # 使用AI总结描述
            prompt = f"""请将以下文本总结为不超过600个字符的简洁描述：

            原文：
                {description}

                要求：
                1. 保留最关键和最具信息量的内容
                2. 使用简洁明了的语言
                3. 保持原文的主要观点和核心信息
                4. 如果有具体的数字、日期或专有名词，请优先保留
                5. 确保总结后的文本连贯流畅，易于理解

                请直接给出总结，无需其他解释。"""
            summarized_description = await ai_chat_async(prompt, model="gpt-4o-mini")
            
            # 更新节点的描述
            graph.nodes[node]['description'] = summarized_description.strip()

    nx.write_graphml(graph, f"{graph_path[:-8]}_summarized.graphml")

    return graph
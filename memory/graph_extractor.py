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

from lib.ai import ai_chat, ai_chat_async
from memory.prompt.prompt_entities import UNTYPED_ENTITY_RELATIONSHIPS_GENERATION_PROMPT
from tqdm.asyncio import tqdm

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

        import vector_db
        node_ids = list(graph.nodes())
        db = vector_db.VectorDB(db_path='./chroma_entities')
        db.upsert_entities(node_ids)


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

from collections import defaultdict
import json
from typing import Dict, Set, List, Tuple

class KnowledgeGraph:
    def __init__(self):
        self.entities: Dict[str, Dict[str, Set[str]]] = defaultdict(self._default_dict)
        self.reverse_entities: Dict[str, Dict[str, Set[str]]] = defaultdict(self._default_dict)

    @staticmethod
    def _default_dict():
        return defaultdict(set)

    def import_from_json(self, json_str: str):
            data = json.loads(json_str)
            
            # 导入关系（三元组）
            for relationship in data['relationships']:
                self.add_triple(relationship['subject'], relationship['predicate'], relationship['object'])
 
    def add_triple(self, subject: str, predicate: str, object: str):
        self.entities[subject][predicate].add(object)
        self.reverse_entities[object][predicate].add(subject)

    def get_triples_by_subject(self, subject: str) -> List[Tuple[str, str, str]]:
        return [(subject, pred, obj) 
                for pred, objs in self.entities[subject].items() 
                for obj in objs]

    def get_triples_by_object(self, object: str) -> List[Tuple[str, str, str]]:
        return [(subj, pred, object) 
                for pred, subjs in self.reverse_entities[object].items() 
                for subj in subjs]

    def get_triples_by_predicate(self, predicate: str) -> List[Tuple[str, str, str]]:
        return [(subj, predicate, obj) 
                for subj, preds in self.entities.items() 
                if predicate in preds
                for obj in preds[predicate]]

    def get_objects(self, subject: str, predicate: str) -> Set[str]:
        return self.entities[subject][predicate]

    def get_subjects(self, predicate: str, object: str) -> Set[str]:
        return self.reverse_entities[object][predicate]

    def __iter__(self):
        for subject, predicates in self.entities.items():
            for predicate, objects in predicates.items():
                for object in objects:
                    yield (subject, predicate, object)

    def save_to_file(self, filename: str):
        import pickle
        with open(filename, 'wb') as f:
            pickle.dump((dict(self.entities), dict(self.reverse_entities)), f)

    @classmethod
    def load_from_file(cls, filename: str):
        import pickle
        with open(filename, 'rb') as f:
            entities_dict, reverse_entities_dict = pickle.load(f)
        kg = cls()
        kg.entities = defaultdict(cls._default_dict, entities_dict)
        kg.reverse_entities = defaultdict(cls._default_dict, reverse_entities_dict)
        return kg
    


def test_save_and_load_kg():
    # 创建一个新的 KnowledgeGraph 实例
    kg = KnowledgeGraph()

    # 添加一些测试数据
    kg.add_triple("Alice", "knows", "Bob")
    kg.add_triple("Alice", "likes", "Chocolate")
    kg.add_triple("Bob", "likes", "Ice Cream")

    # 保存到文件
    filename = 'kg-test.pkl'
    kg.save_to_file(filename)
    print(f"KnowledgeGraph saved to {filename}")

    # 从文件加载
    loaded_kg = KnowledgeGraph.load_from_file(filename)
    print(f"KnowledgeGraph loaded from {filename}")

    # 验证加载的数据
    print("\nVerifying loaded data:")
    print("Triples in loaded KnowledgeGraph:")
    for triple in loaded_kg:
        print(f"- {triple}")

    # 验证特定查询
    print("\nVerifying specific queries:")
    alice_knows = loaded_kg.get_objects("Alice", "knows")
    print(f"Alice knows: {alice_knows}")

    bob_likes = loaded_kg.get_objects("Bob", "likes")
    print(f"Bob likes: {bob_likes}")

    likes_chocolate = loaded_kg.get_subjects("likes", "Chocolate")
    print(f"Who likes Chocolate: {likes_chocolate}")

    # 验证实体和反向实体结构
    print("\nVerifying entity structures:")
    print("Entities:", dict(loaded_kg.entities))
    print("Reverse Entities:", dict(loaded_kg.reverse_entities))

if __name__ == "__main__":
    # 运行测试
    test_save_and_load_kg()
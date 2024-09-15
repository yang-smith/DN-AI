import re
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions
import json

class VectorDB:
    def __init__(self, db_path, collection_name = 'collection'):
        self.em = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="shibing624/text2vec-base-chinese")
        self.client = chromadb.PersistentClient(db_path)
        self.collection = self.init_collections(collection_name)

    def init_collections(self, collection_name):
        try:
            collection = self.client.create_collection(name=collection_name, embedding_function=self.em)
        except:  # already exist collection
            collection = self.client.get_collection(name=collection_name, embedding_function=self.em)

        return collection

    def upsert_document(self, document, id):
        if isinstance(document, dict):
            content = document.get('page_content', '')
            metadata = document.get('metadata', {})
        else:
            content = document.page_content
            metadata = document.metadata

        self.collection.upsert(
            documents=[content],
            metadatas=[metadata],
            ids=[str(id)]
        )
    def upsert_entities(self, entities):
        
        for entity in entities:
            self.collection.upsert(
                    documents=[entity],
                    ids=[entity]
                )
            
    def query_entities(self, user_input, n_results = 30, threshold = 330):
        
        results = self.collection.query(query_texts=[user_input], n_results=n_results)
        filtered_ids = []
        filtered_distances = []
        filtered_documents = []

        for i, distance in enumerate(results['distances'][0]):
            if distance < threshold:
                filtered_ids.append(results['ids'][0][i])
                filtered_distances.append(distance)
                filtered_documents.append(results['documents'][0][i])

        filtered_results = {
            'ids': [filtered_ids],
            'distances': [filtered_distances],
            'documents': [filtered_documents]
        }

        return filtered_ids
            
    def get_records_by_time(self, collection, start, end):
        collection = self.collection if collection == "chat_collection" else self.collection_DN
        start_timestamp = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end, "%Y-%m-%d").timestamp())
        if (end_timestamp - start_timestamp) > 86400 * 2:
            return "查询日期范围太长了"
        if start_timestamp == end_timestamp:
            end_timestamp += 86400

        results = collection.get(where={'$and': [{'timestamp': {"$gte": start_timestamp}}, {'timestamp': {"$lte": end_timestamp}}]})
        formatted_output = ""
        for i in range(len(results['ids'])):
            date_time = datetime.fromtimestamp(results['metadatas'][i]['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            speaker = results['metadatas'][i]['speaker']
            document = results['documents'][i]
            formatted_output += f"{date_time} {speaker}\n{document}\n\n"
        return formatted_output

    def query_by_similar_search(self, user_input, n_results=10, threshold=370):
        results = self.collection.query(query_texts=[user_input], n_results=n_results)
        
        filtered_ids = []
        filtered_distances = []
        filtered_metadatas = []
        filtered_documents = []

        for i, distance in enumerate(results['distances'][0]):
            if distance < threshold:
                filtered_ids.append(results['ids'][0][i])
                filtered_distances.append(distance)
                filtered_metadatas.append(results['metadatas'][0][i])
                filtered_documents.append(results['documents'][0][i])

        filtered_results = {
            'ids': [filtered_ids],
            'distances': [filtered_distances],
            'metadatas': [filtered_metadatas],
            'documents': [filtered_documents]
        }

        return filtered_results

# Example Usage
if __name__ == "__main__":
    print()
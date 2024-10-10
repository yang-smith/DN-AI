
from datetime import datetime
import walnut.memory.vector_db
import walnut.memory.sqlite_db
from langchain_core.documents import Document

class DB:
    def __init__(self, sqlitedb_path = "./documents.db", vecdb_path="./chroma_test"):
        self.sqlitedb = walnut.memory.sqlite_db.SqliteDB(sqlitedb_path)
        self.vecdb = walnut.memory.vector_db.VectorDB(vecdb_path)
    
    def insert_documents(self, documents):
        self.validate_and_prepare_documents(documents)
        docs = []
        for doc in documents:
            try: 
                id = self.sqlitedb.insert_document(doc)
                print(id)
                self.vecdb.upsert_document(doc, id)
                docs.append({'id':id, 'page_content': doc.page_content})
            except:
                print("add documents error")
        return docs

    def insert_documents_test(self, documents):
        self.validate_and_prepare_documents(documents)
        docs = []
        for doc in documents:
            id = self.sqlitedb.insert_document(doc)
            print(id)
            self.vecdb.upsert_document(doc, id)
        return docs

    def get_documents(self, documents):
        docs = []
        for i, doc in enumerate(documents):
            try: 
                id = i +1
                docs.append({'id':id, 'page_content': doc.page_content, 'metadata': doc.metadata})
            except:
                print("get documents error")
        return docs

    def query_by_time(self, start, end, user_input, n_results=10, threshold=370):
        start_timestamp = int(datetime.strptime(start, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end, "%Y-%m-%d").timestamp()) 
        
        result_sq = self.sqlitedb.query_documents_by_time_range(start_timestamp, end_timestamp, user_input)
        result_vec = self.vecdb.query_records_by_time(start_timestamp, end_timestamp, user_input, n_results, threshold)
        print(result_vec)

        for i, id in enumerate(result_vec['ids'][0]):
            if id not in result_sq['ids']:
                result_sq['ids'][0].append(id)
                result_sq['distances'][0].append(result_vec['distances'][0][i])
                result_sq['metadatas'][0].append(result_vec['metadatas'][0][i])
                result_sq['documents'][0].append(result_vec['documents'][0][i])

        return result_sq

    def query(self, content, n_results = 10, threshold = 370):
        result_sq = self.sqlitedb.query_documents_by_content_partial(content)
        result_vec = self.vecdb.query_by_similar_search(content, n_results, threshold)
        
        for i, id in enumerate(result_vec['ids'][0]):
            if id not in result_sq['ids']:
                result_sq['ids'][0].append(id)
                result_sq['distances'][0].append(result_vec['distances'][0][i])
                result_sq['metadatas'][0].append(result_vec['metadatas'][0][i])
                result_sq['documents'][0].append(result_vec['documents'][0][i])

        return result_sq
    
    def close(self):
        self.sqlitedb.close()
    
    def validate_and_prepare_documents(self, documents: list[Document]) -> list[Document]:
        for document in documents:
            if not isinstance(document, Document):
                raise ValueError("Input must be a Langchain Document object")
    
            if not document.page_content:
                raise ValueError("Document must have page_content")

            if not document.metadata:
                document.metadata = {}
    
            if 'source' not in document.metadata:
                raise ValueError("Document metadata must contain 'source'")
    
            if 'timestamp' not in document.metadata:
                document.metadata['timestamp'] = 0
        
        return documents

if __name__ == "__main__":
    import loader
    import graph_extractor
    db = DB()
    documents = loader.load_documents()
    docs = db.insert_documents(documents=documents)
    extractor = graph_extractor.GraphExtractor()
    extractor.extract_graph(docs)


    while 1:
        user_input = input("问点什么：")
        if user_input == "exit":
            break

        time_start = datetime.now()  

        results = db.query(user_input)

        print(results)

        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
        


    db.close()
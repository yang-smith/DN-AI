
from datetime import datetime
import memory.vector_db
import memory.sqlite_db


class DB:
    def __init__(self):
        self.sqlitedb = memory.sqlite_db.SqliteDB('documents.db')
        self.vecdb = memory.vector_db.VectorDB()
    
    def insert_documents(self, documents):
        docs = []
        for doc in documents:
            try: 
                id = self.sqlitedb.insert_document(doc)
                self.vecdb.upsert_document(doc, id)
                docs.append({'id':id, 'page_content': doc.page_content})
            except:
                print("add documents error")
        return docs

    def get_documents(self, documents):
        docs = []
        for i, doc in enumerate(documents):
            try: 
                id = i +1
                docs.append({'id':id, 'page_content': doc.page_content})
            except:
                print("add documents error")
        return docs

    def query(self, content):
        result_sq = self.sqlitedb.query_documents_by_content_partial(content)
        result_vec = self.vecdb.query_by_similar_search(content)
        
        for i, id in enumerate(result_vec['ids'][0]):
            if id not in result_sq['ids']:
                result_sq['ids'][0].append(id)
                result_sq['distances'][0].append(result_vec['distances'][0][i])
                result_sq['metadatas'][0].append(result_vec['metadatas'][0][i])
                result_sq['documents'][0].append(result_vec['documents'][0][i])

        return result_sq
    
    def close(self):
        self.sqlitedb.close()

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
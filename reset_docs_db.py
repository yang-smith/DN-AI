import asyncio
from datetime import datetime
import memory.loader
import memory.graph_extractor
import memory.db
import os
import networkx as nx


# 定义目录路径
dir_path = './records_db'
# dir_path = './customer_services_db'

# 如果目录不存在，创建它
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
    print(f"Created directory: {dir_path}")

db = memory.db.DB(sqlitedb_path=f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
documents1 = memory.loader.load_all_documents()
# documents2 = memory.loader.load_records_documents()
# print(documents2)
# docs1 = db.get_documents(documents=documents1)
# docs2 = db.get_documents(documents=docs)
db.insert_documents(documents=documents1)

# extractor = memory.graph_extractor.GraphExtractor()
# asyncio.run(extractor.extract_graph(docs1, file_path=f"{dir_path}/records.graphml"))

# file_path = f"{dir_path}/records.graphml"
# if os.path.exists(file_path):
#     graph = nx.read_graphml(file_path)
#     extractor.set_entities_db(graph, f"{dir_path}/entities")

# db.close()

async def main():
    while True:
        user_input = input("问点什么：")
        if user_input == "exit":
            break

        time_start = datetime.now()  

        results = db.query(user_input)
        print(results)

        # entities_db = memory.vector_db.VectorDB(db_path=f"{dir_path}/entities")

        # rsp = await query('11',user_input, graph, model='claude-3-haiku-20240307',entities_db=entities_db, db=db)
        # print(rsp)

        time_end = datetime.now() 
        print(f"{round((time_end - time_start).total_seconds(), 2)}s") 
    
# if __name__ == "__main__":
#     asyncio.run(main())
#     db.close()

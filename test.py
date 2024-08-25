

import asyncio
from datetime import datetime
import memory.loader
import memory.graph_extractor
import memory.db

db = memory.db.DB()
documents = memory.loader.load_documents()
docs = db.get_documents(documents=documents)
print(docs)
extractor = memory.graph_extractor.GraphExtractor()
asyncio.run(extractor.extract_graph(docs))


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
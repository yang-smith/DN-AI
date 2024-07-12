
import re
from datetime import datetime


def read_chat_records() -> list:
    """从txt中读取聊天记录,返回聊天记录列表"""
    chat_records = []

    with open('chat_records.txt', 'r', encoding='utf-8') as file:
        current_record = None
        for line in file:
            # 匹配时间和发言人
            match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)', line)
            if match:
                # 如果有当前记录未保存，先保存当前记录
                if current_record:
                    chat_records.append(current_record)
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                timestamp_int = int(timestamp.timestamp())
                speaker = match.group(2)
                current_record = {'timestamp': timestamp_int, 'speaker': speaker, 'message': ''}
            elif current_record:
                # 处理多行消息
                current_record['message'] += line.strip() + '\n'
        # 添加最后一条记录
        if current_record:
            chat_records.append(current_record)

    # 移除每条消息末尾多余的换行符
    for record in chat_records:
        record['message'] = record['message'].strip()

    # 打印解析结果以验证
    for record in chat_records:
        print(record)
    print(len(chat_records))
    return chat_records


import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions

# model = SentenceTransformer("shibing624/text2vec-base-chinese")

# class MyEmbeddingFunction(EmbeddingFunction):
#     def __call__(self, texts: Documents) -> Embeddings:
#         embeddings = [model.encode(x) for x in texts]
#         return embeddings
def init_db():
    em = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="shibing624/text2vec-base-chinese")

    chroma_client = chromadb.PersistentClient("./chroma")
    try:
        collection = chroma_client.create_collection(name="chat_collection", embedding_function=em)
    except:  # already exist collection
        collection = chroma_client.get_collection(name="chat_collection", embedding_function=em)

    try:
        collection_DN = chroma_client.create_collection(name="DN_collection", embedding_function=em)
    except:  # already exist collection
        collection_DN = chroma_client.get_collection(name="DN_collection", embedding_function=em)

    return collection,collection_DN

# chat_records = read_chat_records()
# id = 0
# for record in chat_records:
#     collection.upsert(
#         documents=[record['message']],
#         metadatas=[{"timestamp": record['timestamp'], "speaker": record['speaker']}],
#         ids=[str(id)]
#     )
#     id+=1

def get_records_by_time(collection, start, end):
    start_timestamp = int(datetime.strptime(start,"%Y-%m-%d").timestamp())
    end_timestamp = int(datetime.strptime(end,"%Y-%m-%d").timestamp())
    print(start_timestamp)
    print(end_timestamp)
    if (end_timestamp - start_timestamp) > 86400*2:
        return "需要查询的日期范围太长了"
    if start_timestamp == end_timestamp:
        end_timestamp += 86400
    if collection:
        results = collection.get(where = {'$and':[
                        {'timestamp': {
                                "$gte": start_timestamp}
                        }, 
                        {'timestamp': {
                                "$lte": end_timestamp}
                        }]
                    })
        data = results
        formatted_output = ""
        for i in range(len(data['ids'])):
            date_time = datetime.fromtimestamp(data['metadatas'][i]['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            speaker = data['metadatas'][i]['speaker']
            document = data['documents'][i]
            formatted_output += f"{date_time} {speaker}\n{document}\n\n"
    return formatted_output


def get_records_by_similar_search(collection, user_input, n_results=10):
    results = collection.query(
    query_texts=[user_input],
    n_results=n_results
    )
    data = results
    formatted_output = ""
    for i in range(len(data['ids'][0])):
        date_time = datetime.fromtimestamp(data['metadatas'][0][i]['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        speaker = data['metadatas'][0][i]['speaker']
        document = data['documents'][0][i]
        formatted_output += f"{date_time} {speaker}\n{document}\n\n"

    # print(formatted_output)
    return formatted_output

def get_document_by_similar_search(collection, user_input, n_results=5):
    results = collection.query(
    query_texts=[user_input],
    n_results=n_results
    )
    data = results
    formatted_output = ""
    for i in range(len(data['ids'][0])):
        document = data['documents'][0][i]
        formatted_output += f"{document}\n"

    # print(formatted_output)
    return formatted_output


collection, collection_DN = init_db()




def add_DN_documents():
    from langchain_community.document_loaders import DirectoryLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    source_urls = {
        'base.md': 'https://docs.qq.com/doc/DZGllZ1h5UU1ITlZk',
        'dianping.md': 'https://docs.qq.com/doc/DWWpkb0FqY0NiWXlT', 
        'whatisDN.md': 'http://example.com/whatisDN',
        'yucun.md': 'https://docs.qq.com/doc/DWVRPeVpGb0xJWVlr'
    }

    loader = DirectoryLoader('./documents', glob="**/*.md")
    docs = loader.load()
    for doc in docs:
        metadata = doc.metadata
        filename = metadata['source'].replace('documents\\', '')
        metadata['source'] = source_urls[filename]
        
    # print(docs)

    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.split_documents(docs)
    # print(texts)
    for text in texts:
        print(text)

    em = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="shibing624/text2vec-base-chinese")

    chroma_client = chromadb.PersistentClient("./chroma")
    # chroma_client.delete_collection(name="DN_collection")
    try:
        collection_DN = chroma_client.create_collection(name="DN_collection", embedding_function=em)
    except:  # already exist collection
        collection_DN = chroma_client.get_collection(name="DN_collection", embedding_function=em)

    id = 0
    for text in texts:
        collection_DN.upsert(
            documents=[text.page_content],
            metadatas=[text.metadata],
            ids=[str(id)]
        )
        id+=1
    print("done")
# add_DN_documents()


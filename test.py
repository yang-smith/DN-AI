
# from langchain.vectorstores import Chroma
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.prompts import ChatPromptTemplate
# from langchain.chat_models import ChatOpenAI
# from langchain.schema.runnable import RunnablePassthrough
# from langchain.schema.output_parser import StrOutputParser



import re
from datetime import datetime

def chat():
    # 聊天记录列表
    chat_records = []

    # 读取文件
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
    return collection

# chat_records = chat()
# id = 0
# for record in chat_records:
#     collection.upsert(
#         documents=[record['message']],
#         metadatas=[{"timestamp": record['timestamp'], "speaker": record['speaker']}],
#         ids=[str(id)]
#     )
#     id+=1

from ai import ai_chat

collection = init_db()
while 1:
    user_input = input("问点什么：")
    if user_input == "exit":
        break
    results = collection.query(
        query_texts=[user_input],
        n_results=10
    )

    print(results['documents'])
    print(str(results['documents']))


# db = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory='./persist')

# def show_search(query):
#     results = db.similarity_search(query)
#     # results = db.similarity_search_with_relevance_scores(query)
#     result_str = ""
#     # print(results)
    
#     for result in results:
#         print(result.page_content)
#         print("\n"+"-"*30 + "\n")
#         result_str += result.page_content
#     return result_str

# retriever = db.as_retriever()
# model = ChatOpenAI(model="gpt-4")
# # question = "历代经济变革里说了什么内容"
# # question = "我想写一篇如何学习新领域相关的文章"
# # question = "我想找一首诗，关于爱，自我，他人相关，但是我记不清了"
# question = "请参考王维的诗，分析并尝试仿写一个关于流水主题，格式为七言绝句的诗"
# # question = "请仿写一首诗，要求格式为七言绝句，主题为秋天"

# prompt1 = """
# #### 背景
# 我拥有一个专业的向量数据库，其中储存了众多用户的收藏与笔记内容。

# #### 目的
# 当用户提出问题或输入信息时，为其生成关键搜索词，助其在向量数据库中高效地查找相关资料。

# #### 策略
#     1. 准确把握用户的实际需求。
#     2. 删除问题中无意义文本，保留有助于查询的部分
#     3. 从多维度出发，构建搜索的关键文本。

# #### 注意事项
# take a deep breath and think step by step. 保证内容在50字以内

# #### 用户输入
# {question}

# #### 输出要求
# 仅提供与问题紧密相关的搜索关键词，避免冗余信息。
# """
# prompt_before = ChatPromptTemplate.from_template(prompt1)

# chain_before = prompt_before | model
# content = ""
# for s in chain_before.stream({"question": question}):
#     print(s.content, end="")
#     content += s.content
# print("\n" + "-"*20 + "参考内容如下: \n")
# result_str = show_search(content)



# prompt2 = """
# 参考内容：
# {context}

# Question: {question}

# ####思考步骤
# take a deep breath and think step by step
# 定义问题：首先明确理解所提出的问题。
# 收集信息：查看并理解提供的参考内容。
# 分析信息：分析参考内容，确定其风格、语气,表达结构，以及有助于回答问题的部分。
# 提出假设：基于参考内容提出一个初步的答案。
# 测试假设：检查这个答案是否有效地回答了问题，并保持了参考内容的风格和语气。
# 得出结论：如果这个答案能够有效回答问题，则输出回答。如果不足以回答问题，从头开始重新思考。

# 限制条件
# GPT需要准确判断参考内容是否与提出的问题相关。
# 在答案中应保持参考内容的风格和语气。
# 不要说出思考过程
# 回答使用问题对应的语言。
# """

# prompt = ChatPromptTemplate.from_template(prompt2)


# chain = (
#      prompt
#     | model
#     # | StrOutputParser()
# )

# print("Robot say:")
# for s in chain.stream({"context": result_str, "question": question}):
#     print(s.content, end="")
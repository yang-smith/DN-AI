from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
import os
from langchain_core.documents import Document
from typing import List, Dict
import re
from datetime import datetime

source_urls = {
    'base.md': 'https://docs.qq.com/doc/DZGllZ1h5UU1ITlZk',
    'dianping.md': 'https://docs.qq.com/doc/DWWpkb0FqY0NiWXlT', 
    'whatisDN.md': 'http://example.com/whatisDN',
    'yucun.md': 'https://docs.qq.com/doc/DWVRPeVpGb0xJWVlr'
}

def load_documents(source_urls = source_urls, path = './documents', chunk_size = 300):
    """加载目录下所有md文件，并进行分割。返回List[Document] """
    loader = DirectoryLoader(path, glob="**/*.md")
    docs = loader.load()
    for doc in docs:
        metadata = doc.metadata
        filename = metadata['source'].split('\\')[-1]
        metadata['source'] = source_urls[filename]
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.split_documents(docs)
    return texts

def load_yucun_documents(source_urls = source_urls, path = './documents', chunk_size = 300):
    """加载目录下yucun.md """
    loader = DirectoryLoader(path, glob="**/yucun.md")
    docs = loader.load()
    for doc in docs:
        metadata = doc.metadata
        filename = metadata['source'].split('\\')[-1]
        metadata['source'] = source_urls[filename]
        
    text_splitter = CharacterTextSplitter(
        separator="\n\n",  # 使用双换行符作为分割符
        chunk_size=1000,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.split_documents(docs)
    return texts

def load_summarize_documents(path='./summarize_results', chunk_size=300):
    """加载summarize_results目录下所有txt文件，并进行分割。返回List[Document] """
    loader = DirectoryLoader(path, glob="**/*.txt")
    docs = loader.load()
    
    for doc in docs:
        filename = os.path.basename(doc.metadata['source'])
        date = filename.split('_')[1].split('.')[0]
        doc.metadata['source'] = date
    
    text_splitter = CharacterTextSplitter(
        separator="\n",  
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
    )

    texts = text_splitter.split_documents(docs)
    return texts

def load_all_documents(path_records='./summarize_results', chunk_size=300, source_urls = source_urls, path_doc = './documents'):
    """加载所有文档，包括summarize_results和documents"""
    texts = load_summarize_documents(path_records, chunk_size)
    docs = load_documents(source_urls, path_doc, chunk_size)
    texts.extend(docs)
    return texts

def clean_content(content: str) -> str:
    # 移除所有的时间戳
    cleaned = re.sub(r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] ', '', content)
    # 移除多余的换行符
    cleaned = re.sub(r'\n+', '\n', cleaned)
    return cleaned.strip()

def load_records_documents(path='./monthly_records', chunk_size=300):
    """加载monthly_records目录下所有txt文件，并进行分割。返回List[Document] """
    loader = DirectoryLoader(path, glob="**/*.txt")
    docs = loader.load()
    
    for doc in docs:
        filename = os.path.basename(doc.metadata['source'])
        date = filename.split('_')[1].split('.')[0]
        doc.metadata['source'] = date
    
    text_splitter = CharacterTextSplitter(
        separator="\n",  
        chunk_size=300,
        chunk_overlap=50,
        length_function=len,
    )

    texts = text_splitter.split_documents(docs)
    return texts

def load_ac_records_documents(path: str = './monthly_records', chunk_size=80) -> List[Document]:
    documents = []
    for filename in os.listdir(path):
        if filename.endswith('.txt'):
            file_path = os.path.join(path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            current_doc = ""
            current_timestamp = ""
            timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                timestamp_match = re.match(timestamp_pattern, line)
                if timestamp_match:
                    timestamp = timestamp_match.group(1)
                    content = line[len(timestamp_match.group(0)):].strip()
                    
                    if len(current_doc) + len(content) + 1 > chunk_size:
                        if current_doc:
                            timestamp_int = int(datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S").timestamp())
                            documents.append(Document(page_content=current_doc.strip(), metadata={'timestamp': timestamp_int}))
                        current_doc = content + "\n"
                        current_timestamp = timestamp
                    else:
                        if not current_doc:
                            current_timestamp = timestamp
                        current_doc += content + "\n"
                else:
                    if len(current_doc) + len(line) + 1 > chunk_size:
                        if current_doc:
                            timestamp_int = int(datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S").timestamp())
                            documents.append(Document(page_content=current_doc.strip(), metadata={'timestamp': timestamp_int}))
                        current_doc = line + "\n"
                    else:
                        current_doc += line + "\n"
            
            if current_doc:
                timestamp_int = int(datetime.strptime(current_timestamp, "%Y-%m-%d %H:%M:%S").timestamp())
                documents.append(Document(page_content=current_doc.strip(), metadata={'timestamp': timestamp_int}))
    
    cleaned_documents = []
    for doc in documents:
        cleaned_content = clean_content(doc.page_content)
        cleaned_documents.append(Document(page_content=cleaned_content, metadata=doc.metadata))
    
    return cleaned_documents
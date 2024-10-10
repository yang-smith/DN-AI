from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
import os
from langchain_core.documents import Document
from typing import List, Dict
import re
from datetime import datetime, timedelta

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


def load_ac_records_documents(path: str = './monthly_records', target_chars=100, max_time_diff=timedelta(minutes=20)) -> List[Document]:
    documents = []
    timestamp_pattern = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]')

    for filename in os.listdir(path):
        if not filename.endswith('.txt'):
            continue

        file_path = os.path.join(path, filename)
        buffer = []
        current_timestamp = None

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue

                    timestamp_match = timestamp_pattern.match(line)
                    if timestamp_match:
                        new_timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                        content = clean_content(line[len(timestamp_match.group(0)):].strip())

                        if current_timestamp and (len(''.join(buffer)) >= target_chars or new_timestamp - current_timestamp > max_time_diff):
                            documents.append(create_document('\n'.join(buffer), current_timestamp, filename))
                            buffer = []

                        if not current_timestamp or new_timestamp - current_timestamp > max_time_diff:
                            current_timestamp = new_timestamp

                        buffer.append(content + '\n')  
                    else:
                        buffer.append(clean_content(line) + '\n')  

                if buffer:
                    documents.append(create_document('\n'.join(buffer), current_timestamp, filename))

        except IOError as e:
            print(f"Error reading file {filename}: {e}")
        except Exception as e:
            print(f"Unexpected error processing file {filename}: {e}")

    return documents

def create_document(content: str, start_timestamp: datetime, filename: str) -> Document:
    return Document(
        page_content=content.strip(),
        metadata={
            'timestamp': int(start_timestamp.timestamp()),
            'source': filename
        }
    )


from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

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

def load_records_documents(path='./summarize_results', chunk_size=300):
    """加载summarize_results目录下所有txt文件，并进行分割。返回List[Document] """
    loader = DirectoryLoader(path, glob="**/*.txt")
    docs = loader.load()
    
    for doc in docs:
        filename = os.path.basename(doc.metadata['source'])
        date = filename.split('_')[1].split('.')[0]
        doc.metadata['source'] = date
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.split_documents(docs)
    return texts

def load_all_documents(path_records='./summarize_results', chunk_size=300, source_urls = source_urls, path_doc = './documents'):
    """加载所有文档，包括records和documents"""
    texts = load_records_documents(path_records, chunk_size)
    docs = load_documents(source_urls, path_doc, chunk_size)
    texts.extend(docs)
    return texts
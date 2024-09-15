from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
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

def clean_timestamp(timestamp):
    """清理时间戳中的换行符和多余空格"""
    return re.sub(r'\s+', ' ', timestamp).strip()

def custom_split_records(text, metadata):
    pattern = r'\[(\d{4}\s*\n*\s*\d{2}\s*\n*\s*\d{2}\s*\d{2}:\d{2}:\d{2})\](.*?)(?=\[\d{4}|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    return [Document(page_content=f'[{clean_timestamp(timestamp)}]{content.strip()}', metadata=metadata) for timestamp, content in matches]


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
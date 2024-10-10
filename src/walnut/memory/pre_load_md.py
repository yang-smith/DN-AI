from langchain_text_splitters import MarkdownHeaderTextSplitter
import semchunk
import os
import re
from collections import defaultdict


def pre_load_md(folder_path):
    """ 预处理公众号文章，删除图片链接，分割为信息块。 返回 List[Document] """
    all_chunks = process_markdown_files(folder_path)
    merged_chunks = merge_similar_chunks(all_chunks)
    return merged_chunks


def remove_image_links(text):
    pattern1 = r'!\[.*?\]\(.*?\)'
    cleaned_text = re.sub(pattern1, '', text)

    pattern2 = r'\[.*?\]\(http:.*?\)'
    cleaned_text = re.sub(pattern2, '', cleaned_text)

    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
    return cleaned_text.strip()

def read_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取文件 '{file_path}' 时发生错误: {str(e)}")
        return None

def process_markdown_files(folder_path, threshold = 40, chunk_size = 500):
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("**", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        return_each_line=False,
        strip_headers=False
    )

    chunker = semchunk.chunkerify('shibing624/text2vec-base-chinese', chunk_size) 

    all_chunks = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            file_path = os.path.join(folder_path, filename)
            text = read_markdown_file(file_path)
            if text:
                text = remove_image_links(text)
                md_header_splits = markdown_splitter.split_text(text)
                
                # 合并短块
                merged_splits = []
                for split in md_header_splits:
                    if merged_splits and len(split.page_content.strip()) < threshold:
                        merged_splits[-1].page_content += "\n" + split.page_content
                    else:
                        split.metadata['source'] = filename  
                        merged_splits.append(split)

                # 对合并后的块进行进一步分割
                for merged_split in merged_splits:
                    chunks = chunker(merged_split.page_content)
                    for chunk in chunks:
                        new_chunk = merged_split.copy()
                        new_chunk.page_content = chunk
                        all_chunks.append(new_chunk)
    return all_chunks

def print_chunks_se(chunks):
    print("Chunked text:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print("-" * 40)
        print(chunk.strip())
        print("-" * 40)

def merge_similar_chunks(chunks):
    content_dict = defaultdict(list)
    for chunk in chunks:
        content = chunk.page_content.strip()
        content_dict[content].append(chunk)
    
    merged_chunks = []
    for content, similar_chunks in content_dict.items():
        if len(similar_chunks) > 1:
            # Merge metadata if needed
            merged_chunk = similar_chunks[0]
            merged_chunk.metadata['sources'] = [chunk.metadata.get('source', '') for chunk in similar_chunks]
            merged_chunks.append(merged_chunk)
        else:
            merged_chunks.extend(similar_chunks)
    
    return merged_chunks


def print_chunks(chunks):
    print("Chunked text:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print("-" * 40)
        print(chunk.page_content.strip())
        print("-" * 40)

if __name__ == "__main__":
    folder_path = 'docs/gongzhonghao'
    # all_chunks = process_markdown_files(folder_path)
    # merged_chunks = merge_similar_chunks(all_chunks)

    # print_chunks(merged_chunks)
    # print(f"Total chunks after merging: {len(merged_chunks)}")
    results = pre_load_md(folder_path)
    print(results)

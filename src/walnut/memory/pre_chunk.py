import semchunk
import tiktoken                        # they are here for demonstration purposes.
import re

def remove_image_links(text):
    # 正则表达式匹配Markdown格式的图片链接
    pattern = r'!\[.*?\]\(.*?\)'
    # 使用空字符串替换所有匹配项
    cleaned_text = re.sub(pattern, '', text)
    # 删除可能留下的空行
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
    return cleaned_text.strip()

def read_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取文件 '{file_path}' 时发生错误: {str(e)}")
        return None

chunk_size = 300 # A low chunk size is used here for demonstration purposes. Keep in mind that
               # `semchunk` doesn't take special tokens into account unless you're using a
               # custom token counter, so you probably want to deduct your chunk size by the
                # number of special tokens added by your tokenizer.
file_path = 'docs/documents/dianping.md'
file_path = 'docs/gongzhonghao/9个人来自8个省在银坑村的郭阿姨家做了一餐饭丨ThePlaceLab.md'
file_path = 'docs/gongzhonghao/那座像教堂一样的老房子里住着一位老企业家丨KC在余村.md'

text = read_markdown_file(file_path)
if text:
    text = remove_image_links(text)

# As you can see below, `semchunk.chunkerify` will accept the names of all OpenAI models, OpenAI
# `tiktoken` encodings and Hugging Face models (in that order of precedence), along with custom
# tokenizers that have an `encode()` method (such as `tiktoken`, `transformers` and `tokenizers`
# tokenizers) and finally any function that can take a text and return the number of tokens in it.
# chunker = semchunk.chunkerify('shibing624/text2vec-base-chinese', chunk_size) 
# The resulting `chunker` can take and chunk a single text or a list of texts, returning a list of
# chunks or a list of lists of chunks, respectively.

chunker = semchunk.chunkerify('gpt-4o-mini', chunk_size) 

def print_chunks(chunks):
    print("Chunked text:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print("-" * 40)
        print(chunk.strip())
        print("-" * 40)

print_chunks(chunker(text))
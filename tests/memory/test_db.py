import pytest
import tempfile
import os
from walnut.memory.db import DB
from walnut.memory.pre_load_md import pre_load_md



def test_pre_load_and_insert_to_db():
    # 使用临时文件夹路径创建DB实例
    dir_path = './testDB'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")
    db = DB(sqlitedb_path=f"{dir_path}/sqlite.db", vecdb_path=f"{dir_path}/chroma")
    
    # 使用pre_load_md处理示例Markdown文件
    folder_path = 'docs/gongzhonghao'
    documents = pre_load_md(folder_path)
    
    # 确保pre_load_md返回了文档
    assert len(documents) > 0, "pre_load_md should return some documents"
    
    # 将文档插入数据库
    inserted_docs = db.insert_documents(documents)

    # 尝试查询插入的文档
    query_result = db.query("日用百货", n_results=5)
    print(query_result)

    # 验证查询结果
    assert len(query_result['ids'][0]) > 0, "Query should return some results"
    
    # 清理
    db.close()

# 可以添加更多测试用例来覆盖不同的场景
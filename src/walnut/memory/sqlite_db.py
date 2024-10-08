import json
import sqlite3
from datetime import datetime

class SqliteDB:
    def __init__(self, db_path):
        """
        初始化连接到 SQLite 数据库
        """
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """
        创建文档存储表，如果不存在的话
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_document(self, document):
        """
        插入文档到SQLite数据库
        """
        try:
            cursor = self.conn.cursor()
            if isinstance(document, dict):
                content = document.get('page_content', '')
                metadata = json.dumps(document.get('metadata', {}))
            else:
                content = document.page_content
                metadata = json.dumps(document.metadata)
            
            cursor.execute('INSERT INTO documents (content, metadata) VALUES (?, ?)',
                            (content, metadata))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error inserting document: {e}")
            return None

    def query_document_by_content(self, content):
        """
        根据内容查询文档
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, content, metadata FROM documents WHERE content = ?', (content,))
            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error querying document by content: {e}")
            return []
        
    def query_documents_by_content_partial(self, partial_content):
        """
        根据部分内容查询文档
        """
        try:
            cursor = self.conn.cursor()
            query = f'%{partial_content}%'
            cursor.execute('SELECT id, content, metadata FROM documents WHERE content LIKE ?', (query,))
            results = cursor.fetchall()

            ids = []
            distances = []
            metadatas = []
            contents = []
            for row in results:
                ids.append(row[0])
                contents.append(row[1])
                metadatas.append(row[2])
                distances.append('100')
            sq_results = {
                'ids': [ids],
                'distances': [distances],
                'metadatas': [metadatas],
                'documents': [contents]
            }
            return sq_results
        
        except sqlite3.Error as e:
            print(f"Error querying document by partial content: {e}")
            return []
    
    def query_documents_by_time_range(self, start_time, end_time, partial_content=None, n_results=10):
        """
        根据时间范围和可选的部分内容查询文档
        """
        try:
            cursor = self.conn.cursor()
            query = '''
                SELECT id, content, metadata 
                FROM documents 
                WHERE json_extract(metadata, '$.timestamp') BETWEEN ? AND ?
            '''
            params = [start_time, end_time]

            if partial_content:
                query += ' AND content LIKE ?'
                params.append(f'%{partial_content}%')

            query += ' ORDER BY json_extract(metadata, "$.timestamp") DESC LIMIT ?'
            params.append(n_results)

            cursor.execute(query, params)
            results = cursor.fetchall()

            ids = []
            distances = []
            metadatas = []
            contents = []
            for row in results:
                ids.append(row[0])
                contents.append(row[1])
                metadata = json.loads(row[2])
                metadatas.append(metadata)
                distances.append(0)  # 使用0作为占位符

            return {
                'ids': [ids],
                'distances': [distances],
                'metadatas': [metadatas],
                'documents': [contents]
            }
        
        except sqlite3.Error as e:
            print(f"Error querying documents by time range: {e}")
            return {'ids': [[]], 'distances': [[]], 'metadatas': [[]], 'documents': [[]]}

    def clear_all_documents(self):
        """
        清空所有文档数据
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM documents')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error clearing documents: {e}")

    def delete_document_by_content(self, content):
        """
        删除指定内容的文档
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM documents WHERE content = ?', (content,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting document by content: {e}")

    def close(self):
        """
        关闭数据库连接
        """
        self.conn.close()

if __name__ == "__main__":
    import loader
    db = SqliteDB('documents.db')
    documents = loader.load_documents()
    db.insert_documents(documents=documents)
    results = db.query_documents_by_content_partial('浙江省湖州市安吉县天荒坪镇')
    for row in results:
        print(f"Document ID: {row[0]}, Content: {row[1]}, Metadata: {row[2]}")

    vec_results = db.chroma.query_by_similar_search(user_input='浙江省湖州市安吉县天荒坪镇')
    print(vec_results)

    db.clear_all_documents()
    db.close()

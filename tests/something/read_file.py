import os

def read_python_files(directory):
    all_content = ""
    for root, dirs, files in os.walk(directory):
        py_files = [file for file in files if file.endswith('.py')]
        for py_file in py_files:
            file_path = os.path.join(root, py_file)
            # 添加文件所在目录信息
            all_content += f"Directory: {root}\n\n"
            with open(file_path, 'r', encoding='utf-8') as file:
                all_content += file.read() + "\n\n\n"
    return all_content

# 设置输入路径和输出文件路径
directory_path = r'C:\Users\89206\Downloads\graphrag\graphrag'  # 你的文件夹路径
output_file_path = r'.\all_py_contents.txt'  # 输出文本文件路径

# 读取内容并保存
content = read_python_files(directory_path)
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Content saved to {output_file_path}")

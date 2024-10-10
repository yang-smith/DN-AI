import random
import re

def is_restaurant(info):
    # 检查是否包含"餐厅名称："或"烧烤"等关键词
    return "餐厅名称：" in info or "烧烤" in info

def parse_restaurants(markdown_content):
    # 使用双重换行分割内容
    all_entries = re.split(r'\n\n+', markdown_content)
    # 移除空元素并过滤掉非餐厅信息
    restaurants = [r.strip() for r in all_entries if r.strip() and is_restaurant(r)]
    return restaurants

def extract_restaurant_name(restaurant_info):
    # 使用正则表达式匹配餐厅名称
    name_match = re.search(r'- ([^:]+名称：\s*(.+))', restaurant_info)
    if name_match:
        return name_match.group(2).strip()
    return "未知餐厅"

def random_restaurant_recommendation(markdown_content):
    restaurants = parse_restaurants(markdown_content)
    
    if not restaurants:
        return "没有找到任何餐厅信息。"
    
    # 随机选择一个餐厅
    recommended_restaurant = random.choice(restaurants)
    
    # 提取餐厅名称
    restaurant_name = extract_restaurant_name(recommended_restaurant)
    
    return f"随机推荐的餐厅是：\n\n{restaurant_name}\n\n{recommended_restaurant}"

def multiple_restaurant_recommendations(markdown_content, num_recommendations):
    restaurants = parse_restaurants(markdown_content)
    
    if not restaurants:
        return "没有找到任何餐厅信息。"
    
    # 确保推荐数量不超过可用餐厅数量
    num_recommendations = min(num_recommendations, len(restaurants))
    
    # 随机选择指定数量的餐厅
    recommended_restaurants = random.sample(restaurants, num_recommendations)
    
    recommendations = []
    for restaurant in recommended_restaurants:
        restaurant_name = extract_restaurant_name(restaurant)
        recommendations.append(f"{restaurant_name}\n\n{restaurant}")
    
    return recommendations


def read_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取文件 '{file_path}' 时发生错误: {str(e)}")
        return None

if __name__ == "__main__":
    # 文件路径
    file_path = 'documents/eat.md'

    # 读取文件内容
    markdown_content = read_markdown_file(file_path)

    if markdown_content:
        # 调用函数并打印结果
        print(multiple_restaurant_recommendations(markdown_content, 3)) 
    else:
        print("无法处理文件内容。")
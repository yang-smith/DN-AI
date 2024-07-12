import os
# from lib.ai import ai_chat, run_conversation
# from lib.prompt import prompt_sys, prompt_chat, prompt_test
# from lib.db import collection, collection_DN, get_document_by_similar_search



# record = get_records_by_time(collection=collection, start='2024-03-30', end='2024-03-31')
# print(record)

# test_text = {'ids': [['3347', '3310', '3355', '3354', '3304', '3349', '3353', '3359', '1329', '1308']], 'distances': [[351.62857458033983, 359.8432747121432, 360.08362185765924, 366.3422641882954, 366.44966035607166, 366.72300593119365, 369.2286390126411, 379.529916789775, 381.95648193359375, 381.95648193359375]], 'metadatas': [[{'speaker': '落落不方', 'timestamp': 1715752730}, {'speaker': '小虎。', 'timestamp': 1715750414}, {'speaker': '📟77KUKU77_余村', 'timestamp': 1715755059}, {'speaker': '落落 不方', 'timestamp': 1715754338}, {'speaker': 'Mia_余村', 'timestamp': 1715748509}, {'speaker': '落落不方', 'timestamp': 1715753326}, {'speaker': 'Anna_🍃_余村', 'timestamp': 1715754267}, {'speaker': 'KK_秀帅_余村', 'timestamp': 1715757910}, {'speaker': '十三月杏仁', 'timestamp': 1714313536}, {'speaker': '十三月杏仁', 'timestamp': 1714311532}]], 'embeddings': None, 'documents': [['全能模型🐮', '可以', '#接龙\n今晚七点三十 19：30 尊巴💃🏻🕺🏻🕺🏻💃🏻😄30min\n拉伸+舒缓+入门+跳+拉伸\n\n1. 小初 无门槛 进门就能跳💃🏻🕺🏻💃🏻🕺🏻外加一个强度彩蛋 hiphop风格的加练3min\n2. Mia\n3. 阿银\n4. Anna 🍃\n5. 落落不方\n6. 小 屿·77', '#接龙\n今晚七点三十 19：30 尊巴💃🏻🕺🏻🕺🏻💃🏻😄30min\n拉伸+舒缓+入门+跳+拉伸\n\n1. 小初 无门槛 进门就能跳💃🏻🕺�💃🏻🕺🏻外外加一个强度彩蛋 hiphop风格的加练3min\n2. Mia\n3. 阿银\n4. Anna 🍃\n5. 落落不方', '这个本领需要展开说说，值得学习旺柴]\n引用:YZ:老chen坏的时候看起来也挺好', '开始了', '#接龙\n今晚七点三十 19：30 尊巴💃🏻🕺🏻🕺🏻💃🏻😄30min\n拉伸+舒缓+入门+跳+拉伸\n\n1. 小初 无门槛 进门就能跳💃🏻🕺🏻💃🏻🕺🏻外加一个强度彩蛋 hiphop风格的加练3min\n2. Mia\n3. 阿银\n4. Anna 🍃', '#接龙\nChatGPT-4o体验，今天中午收到了Mac版本邀请，试了下是4o模型语音对话，有兴趣体验的同学可以下午两点来A2会议室。受限于 请求频次，可能需要等待\n\n1. 李其超\n2. 趁早✨ 支持\n3. 落落不方\n4. STELLALALA\n5. Way\n6. Rain 我的账号被 ban 了，回来体 验下\n7. 振中\n8. KK 秀帅', '[图片]', '[图片]']], 'uris': None, 'data': None}

# print(test_text['documents'][0][0])

root = r"C:\Mine\project\DN-AI\DN_AI\lib\site-packages\wcferry"
cmd = fr'"{root}\wcf.exe" start 10086 debug'
print(os.path.exists(root))
print(cmd)
print(os.system(cmd))



# while 1:
#     user_input = input("问点什么：")
#     if user_input == "exit":
#         break
#     # results = collection.query(
#     #     query_texts=[user_input],
#     #     n_results=10
#     # )

#     # # print(results)
#     # print(re_string(results))
#     message = prompt_chat(question=user_input)
#     print(message)
#     # ai_response = ai_chat(message=message, model='gpt-4o')
#     ai_response = run_conversation(message=message)
#     print(ai_response)


# while 1:
#     user_input = input("问点什么：")
#     if user_input == "exit":
#         break
#     results = get_document_by_similar_search(collection_DN, user_input, 4)
#     # print(results)
#     # print(re_string(results))
#     message = prompt_test(question=user_input,ducument=results)
#     print(message)
#     ai_response = ai_chat(message=message, model="gpt-4o")
#     print(ai_response)
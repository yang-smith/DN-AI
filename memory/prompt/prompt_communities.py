


COMMUNITY_REPORT_PROMPT = """You are an AI assistant that helps a human analyst to perform general information discovery. 
Information discovery is the process of identifying and assessing relevant information associated with certain entities (e.g., organizations and individuals) within a network.

# Goal
Write a comprehensive report of a community, given a list of entities that belong to the community as well as their relationships and optional associated claims. The report will be used to inform decision-makers about information associated with the community and their potential impact. The content of this report includes an overview of the community's key entities, their legal compliance, technical capabilities, reputation, and noteworthy claims.

# Report Structure

The report should include the following sections:

- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant information associated with its entities.
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the severity of IMPACT posed by entities within the community.  IMPACT is the scored importance of a community.
- RATING EXPLANATION: Give a single sentence explanation of the IMPACT severity rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format:
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
            ...
        ]
    }}

# Grounding Rules

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

where 1, 5, 7, 23, 2, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.


# Example Input
-----------
Text:
```
Entities
id,entity,description
身份证信息,   身份证信息是入住者必须登记的有效身份证明，包括随行人员和临时入住者
湖州市,   湖州市是浙江省的一个城市，DN余村位于该城市的安吉县  
床品三件套,   床品三件套是指使用过的床上用品，需拆卸并清洗后放回柜子
退房流程,   退房流程是指在离开住宿时需要遵循的步骤和注意事项  
PASSWORD,   The password for the Wi-Fi is 88888888
管理人员,   管理人员是指负责管理住宿的工作人员，客人需将房卡钥匙归还给他们
管理人员负责监督入住者的行为和管理住宿环境，入住者需与其说明情况
房卡,   房卡可用作在地各合作商家的优惠凭证，并在退房时需归还  
安吉数字游民公社（DNA）,   安吉数字游民公社（DNA）是DN余村之前的数字游民公社，提供类似的服务
安吉县,   安吉县是浙江省的一个县，余村位于该县的天荒坪镇      
安吉县是湖州市下辖的一个县，DN余村位于该县的天荒坪镇
两山景区,   两山景区是以“两山”实践为主题的生态旅游和乡村度假景区，位于余村
房间与床位,   房间与床位是入住者使用的住宿设施，不能私下转让或调换
个人物品,   个人物品是指客人在房间内的私有物品，需在退房前清理
DN余村是一个数字游民公社，提供工作和生活的综合园区，强调开放、共建、共享的价值观
DN余村是一个提供住宿的地方，要求入住者遵守特定的入住指南和规定
“DN余村”是“Digital Nomad 余村”的缩写，位于浙江省湖州市安吉县天荒坪镇，是一个数字游民公社
“DN余村”是一个开放的宠物友好社区，提供多种房型选择，包括4人间 、6人间、单人间、双人标准间和家庭房。
DN余村是一个距离天荒坪镇政府步行10分钟的地方。
WI-FI,   “DN余村”提供Wi-Fi服务，名称为DN_2.4和DN_5G，密码为88888888。
客服,   客服负责处理退房相关事宜，并提供帮助和信息
客服负责协调房间和处理入住者的特殊请求。
客服是负责处理入住者问题和安排的人员，入住者需要与其沟通相关事宜
客服是指提供帮助和支持的工作人员，客人需与其沟通退房事宜      
客服负责接收和处理社区内的反馈和报修请求
门禁系统,   入住后，客服会通过微信推送门禁系统的相关信息。    
管理员,   管理员负责管理退房流程，并协助客人完成退房
管理员负责处理社区内的安全问题和反馈
公共空间,   社区内的公共空间需保持良好状态，出现损坏需及时反馈
续订房间,   续订房间是入住者在入住后继续使用房间的请求，需要提前告知客服
垃圾,   垃圾是指在房间内产生的废弃物，需在退房前清理

Relationships
id,source,target,description
身份证信息->DN余村:   入住者必须登记身份证信息以符合入住要求  
湖州市->DN余村:   DN余村位于湖州市安吉县天荒坪镇
床品三件套->退房流程:   退房流程要求拆卸床品三件套并清洗后放回柜子
退房流程->客服:   退房流程中客人需与客服沟通处理退房事宜      
退房流程->个人物品:   退房流程要求客人在退房前清理房间内的个人物品
退房流程->垃圾:   退房流程要求客人在退房前清理房间内的垃圾    
退房流程->管理人员:   退房流程中客人需将房卡钥匙归还给管理人员
PASSWORD->WI-FI:   The Wi-Fi requires the password 88888888 for access
管理人员->DN余村:   管理人员负责监督入住者并处理相关问题      
房卡->客服:   房卡在退房时需归还给客服
安吉数字游民公社（DNA）->DN余村:   DN余村是安吉数字游民公社（DNA）之后建立的第二个数字游民公社
安吉县->DN余村:   DN余村位于安吉县的天荒坪镇
DN余村位于安吉县内
房间与床位->DN余村:   房间与床位是DN余村提供的住宿设施，入住者需遵守使用规定
浙江省->DN余村:   DN余村位于浙江省内
DN余村位于浙江省湖州市安吉县天荒坪镇
DN余村->客服:   客服在“DN余村”中负责协调房间和处理入住者的特殊请求。
入住者需要与客服沟通以处理入住相关事宜
DN余村->WI-FI:   “DN余村”提供Wi-Fi服务，供入住者使用。        
DN余村->门禁系统:   门禁系统在“DN余村”中用于管理入住者的出入。
DN余村->续订房间:   入住者需提前告知客服以续订房间，确保安排顺利
客服->管理员:   客服和管理员共同负责处理退房事宜
管理员和客服共同负责处理社区内的安全和反馈问题
客服->公共空间:   公共空间的损坏需及时反馈给客服进行报修
```
```
Output:
{{
    "title": "DN余村数字游民公社",
    "summary": "DN余村是一个位于浙江省湖州市安吉县天荒坪镇的数字游民公社，提供工作和生活的综合园区。它强调开放、共建、共享的价值观，提供多种房型选择，并设有完善的管理系统，包括客服、管理员、Wi-Fi和门禁系统等。入住者需遵守特定的入住指南和规定，包括 身份登记、房间使用和退房流程等。",
    "rating": 6.5,
    "rating_explanation": "DN余村作为一个创新的数字游民社区， 具有一定的社会和经济影响力，但其影响范围可能仍局限于特定群体。",
    "findings": [
        {{
            "summary": "DN余村的地理位置和背景",
            "explanation": "DN余村位于浙江省湖州市安吉县天荒坪镇，是继安吉数字游民公社（DNA）之后建立的第二个数字游民公社。 它距离天荒坪镇政府步行仅10分钟，地理位置优越。DN余村的全称是'Digital Nomad 余村'，这个名称反映了其作为数字游民聚集地的定位。[Data: Entities (湖州市, 安吉县, DN余村, 安吉数字游民公社（DNA）); Relationships (湖州市->DN余村, 安吉县->DN余村, 安吉数字游民公社（DNA）->DN余村)]"
        }},
        {{
            "summary": "DN余村的核心理念和服务",
            "explanation": "DN余村是一个提供工作和生活综合服务的园区，强调开放、共建、共享的价值观。它是一个宠物友好的社区，提供多种房型选择，包括4人间、6人间、单人间、双人标准间和家庭房，以满足不同入住者的需求。DN余村还提供Wi-Fi服务（名称为DN_2.4 和DN_5G，密码为88888888），为数字游民的工作和生活提供便利。[Data: Entities (DN余村, WI-FI, PASSWORD); Relationships (DN余村->WI-FI)]"
        }},
        {{
            "summary": "入住流程和规定",
            "explanation": "DN余村有严格的入住流程和规定。入住者必须登记有效的身份证信息，包括随行人员和临时入住者。入住后，客服会通过微信推送门禁系统的相关信息。房间和床位不能私下转让或调换，如需续订房间，入住者需提前告知客服。这些规定旨在确保社区的安全和有序运行。[Data: Entities (身份证信息, 房间与床位, 门 禁系统, 续订房间); Relationships (身份证信息->DN余村, 房间与床位->DN余村, DN余村->门禁系统, DN余村->续订房间)]"
        }},
        {{
            "summary": "退房流程和要求",
            "explanation": "DN余村有明确的退房流程和要求。退房时，入住者需要清理个人物品和垃圾，拆卸并清洗床品三件套后放回柜子。房卡需要归还给管理人员或客服，它还可以用作在当地合作商家的优惠凭证。整个退房过程需要与客服和管理员沟通，确保顺利完成。这些要求体现了DN余村对环境维护和资源管理的重视。[Data: Entities (退房流程, 床品三件套, 个人物品, 垃圾, 房卡, 管理人员, 客服); Relationships (退房流程->客服, 退房流程->个人物品, 退房流程-> 垃圾, 退房流程->管理人员, 房卡->客服)]"
        }},
        {{
            "summary": "管理体系和公共空间维护",
            "explanation": "DN余村拥有完善的管理体系，包括客服、管理人员和管理员。客服负责协调房间、处理入住者的特殊请求和退房事宜。管理人员负责监督入住者的行为和管理住宿环境。管理员则负责处理社区内的安全问题和反馈。公共空间的维护也是管理体系的重要部分，入住者需要保持公共空间的良好状态，如发现损坏需及时反馈给客服进行报修。这种管理体系确保了DN余村的有序运营和良好的居住环境。[Data: Entities (管理人员, 客服, 管理员, 公共空间); Relationships (管理人员->DN余村, DN余村->客服, 客服->管理员, 客服-> 公共空间)]"
        }}
    ]
}}


# Real Data

Use the following text for your answer. Do not make anything up in your answer. 

Text:
```
{input_text}
```

The report should include the following sections:

- TITLE: community's name that represents its key entities - title should be short but specific. When possible, include representative named entities in the title.
- SUMMARY: An executive summary of the community's overall structure, how its entities are related to each other, and significant information associated with its entities.
- IMPACT SEVERITY RATING: a float score between 0-10 that represents the severity of IMPACT posed by entities within the community.  IMPACT is the scored importance of a community.
- RATING EXPLANATION: Give a single sentence explanation of the IMPACT severity rating.
- DETAILED FINDINGS: A list of 5-10 key insights about the community. Each insight should have a short summary followed by multiple paragraphs of explanatory text grounded according to the grounding rules below. Be comprehensive.

Return output as a well-formed JSON-formatted string with the following format:
    {{
        "title": <report_title>,
        "summary": <executive_summary>,
        "rating": <impact_severity_rating>,
        "rating_explanation": <rating_explanation>,
        "findings": [
            {{
                "summary":<insight_1_summary>,
                "explanation": <insight_1_explanation>
            }},
            {{
                "summary":<insight_2_summary>,
                "explanation": <insight_2_explanation>
            }}
            ...
        ]
    }}

# Grounding Rules

Points supported by data should list their data references as follows:

"This is an example sentence supported by multiple data references [Data: <dataset name> (record ids); <dataset name> (record ids)]."

Do not list more than 5 record ids in a single reference. Instead, list the top 5 most relevant record ids and add "+more" to indicate that there are more.

For example:
"Person X is the owner of Company Y and subject to many allegations of wrongdoing [Data: Reports (1), Entities (5, 7); Relationships (23); Claims (7, 2, 34, 64, 46, +more)]."

where 1, 5, 7, 23, 2, 34, 46, and 64 represent the id (not the index) of the relevant data record.

Do not include information where the supporting evidence for it is not provided.

其中一个summary是统计summary，给出这个社区中各种统计数据。

Output:
"""
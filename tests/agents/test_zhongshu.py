import pytest
from unittest.mock import patch, MagicMock
from walnut.agents.zhongshu import Zhongshu

pytestmark = pytest.mark.asyncio

@pytest.fixture
def zhongshu():
    return Zhongshu()

@pytest.fixture
def test_id():
    return "test_conversation"

@patch('walnut.utils.ai.ai_chat_AsyncOpenAI')
async def test_query(mock_ai_chat, zhongshu, test_id):
    mock_ai_chat.return_value = "查询后回复"
    result = await zhongshu.query(test_id, "你好，核桃")
    print(result)
    assert result == "查询后回复"
    assert "你好，核桃" in zhongshu.conversations[test_id]

@patch('walnut.utils.ai.ai_chat_AsyncOpenAI')
async def test_check(mock_ai_chat, zhongshu, test_id):
    mock_ai_chat.return_value = "直接回复"
    result = await zhongshu.check(test_id, "核桃，今天天气怎么样？")
    assert result == True

    mock_ai_chat.return_value = "不需回复"
    result = await zhongshu.check(test_id, "用户A：今天天气真好")
    assert result == False

async def test_add_conversation(zhongshu, test_id):
    zhongshu.add_conversation(test_id, "测试消息1")
    zhongshu.add_conversation(test_id, "测试消息2")
    assert len(zhongshu.conversations[test_id]) == 2
    assert zhongshu.conversations[test_id][-1] == "测试消息2"

async def test_clear_conversation(zhongshu, test_id):
    zhongshu.add_conversation(test_id, "测试消息")
    zhongshu.clear_conversation(test_id)
    assert test_id not in zhongshu.conversations

async def test_max_queue_size(zhongshu, test_id):
    for i in range(15):
        zhongshu.add_conversation(test_id, f"消息{i}")
    assert len(zhongshu.conversations[test_id]) == 10
    assert zhongshu.conversations[test_id][0] == "消息5"
    assert zhongshu.conversations[test_id][-1] == "消息14"

import pytest
from unittest.mock import patch, MagicMock
from walnut.agents.baishi import Baishi

pytestmark = pytest.mark.asyncio

async def test_query():
    baishi = Baishi(dir_path='./testDB')
    result1 = await baishi.query("test_conversation", "核桃，早上好啊")
    result2 = await baishi.query("test_conversation", "核桃，你知道十月份有啥好玩的活动吗")
    result3 = await baishi.query("test_conversation", "小枣，你在吗")
    print(result1)
    print(result2)
    print(result3)
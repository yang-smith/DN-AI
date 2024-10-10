import pytest
from walnut.agents.random_restaurant import RandomRestaurant

pytestmark = pytest.mark.asyncio

async def test_query():
    random_restaurant = RandomRestaurant()
    result1 = random_restaurant.query("test_conversation", "核桃，抽签吃饭")
    print(result1)
import agents.baishi as baishi
import agents.customer_services as customer_services
import asyncio

async def main():
    baishi_agent = baishi.Baishi()
    customer_services_agent = customer_services.CustomerServices()
    while True:
        user_input = input("请输入：")
        if user_input == "exit":
            break
        res =await customer_services_agent.query('11', user_input)
        print(res)

if __name__ == "__main__":
    asyncio.run(main())

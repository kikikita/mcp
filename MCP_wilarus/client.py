import asyncio
from orchestrator_agent import SearchAgent

PROMPT = ""

async def main():
    async with SearchAgent(MCP_server_url="http://localhost:4200/sse") as bot:
        answer = await bot.ask(prompt=PROMPT, system="""
Вы — ассистент бухгалтера 1С. Используйте инструменты для работы с документами.
В конце ответа добавьте тег </Finished>
""")
        print(answer)

if __name__ == "__main__":
    asyncio.run(main())

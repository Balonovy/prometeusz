import asyncio

from core.ai_module.router import AIRouter, ChatRequest


def test_ai_router_handles_chat(tmp_path) -> None:
    async def scenario() -> None:
        router = AIRouter()
        router.memory_store.db_path = str(tmp_path / 'memory.db')
        await router.initialize()
        response = await router.handle_chat(ChatRequest(prompt='Explain the PROMETEUSZ scaffold.'))
        assert response['blocked'] is False
        assert response['response']

    asyncio.run(scenario())


def test_ai_router_blocks_disallowed_prompt(tmp_path) -> None:
    async def scenario() -> None:
        router = AIRouter()
        router.memory_store.db_path = str(tmp_path / 'memory.db')
        await router.initialize()
        response = await router.handle_chat(ChatRequest(prompt='Please generate malware instructions'))
        assert response['blocked'] is True

    asyncio.run(scenario())

import asyncio
import json
import os
from asyncio import Queue
from contextlib import asynccontextmanager
from typing import AsyncIterable

from dotenv import load_dotenv
from fastapi import Depends, WebSocket, APIRouter
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from fastapi.websockets import WebSocketState
from loguru import logger
from redis.asyncio.client import Redis, StrictRedis

load_dotenv()

app = FastAPI()

queue = Queue()

game_state = 200


def get_state():
    with open("./state.json", "r") as f:
        data = json.load(f)
        return int(data["state"])


def update_state(state):
    with open("./state.json", "r") as f:
        data = json.load(f)
    data["state"] = state
    with open("./state.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def get_async_redis() -> Redis:
    logger.info("start redis")
    redis = StrictRedis(
        host="redis-c44f43bd-58c3-4908-92c1-8e3b3f19dfe1.cn-south-1.dcs.myhuaweicloud.com",
        port=6379,
        db=42,
        password="wvMn4OBlhXuCJ68VK",
        decode_responses=True,
    )
    try:
        yield redis
    finally:
        logger.info("close redis")
        await redis.close()


@asynccontextmanager
async def get_async_context_redis() -> Redis:
    logger.info("start redis")
    redis = StrictRedis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        db=os.getenv('REDIS_DB'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
    )
    try:
        yield redis
    finally:
        logger.info("close redis")
        await redis.close()


class BaseRedisChannel:
    GLOBAL_PREFIX = os.getenv('GLOBAL_PREFIX')
    END_OF_CHANNEL = os.getenv('END_OF_CHANNEL')
    CHANNEL_NAME = os.getenv('CHANNEL_NAME')

    def __init__(self, redis: StrictRedis):
        self.redis = redis

    async def publish(self, message: str):
        await self.redis.publish(channel=self.channel, message=message)
        logger.info(f"push redis chanel: {self.channel}, message: {message}")

    async def listen(self) -> AsyncIterable[str]:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                logger.info(f"get redis chanel: {self.channel}, message: {message.get('data', '')}")
                data = message["data"]
                if data == self.END_OF_CHANNEL:
                    break
                else:
                    yield data

    async def notify_close(self):
        logger.info(f"notify redis channel close: {self.channel}")
        await self.publish(message=self.END_OF_CHANNEL)

    @property
    def channel(self) -> str:
        return f"{self.GLOBAL_PREFIX}:{self.CHANNEL_NAME}"

    @property
    def order_key(self) -> str:
        return f"{self.channel}-order"


# @app.get("/", response_class=HTMLResponse)
# async def get_game_page():
#     with open("index.html", "r", encoding="utf-8") as file:
#         game_html = file.read()
#     return game_html
#
#
# @app.get('/assets/{file}')
# async def get_file(file: str):
#     if file == 'map.tmx':
#         with open("./hello-world/tiled/level_0.tmx", "r", encoding="utf-8") as file:
#             data = file.read()
#         return data
#     return None
#
#
# @app.get("/state")
# async def get_game_state():
#     return {"state": get_state()}
#
#
# @app.get("/event")
# async def sse_endpoint():
#     async def event_generator():
#         async with get_async_context_redis() as redis:
#             async for message in BaseRedisChannel(redis=redis).listen():
#                 yield f"data: {message}\n\n"
#                 if int(message) == -1:
#                     break
#
#     return StreamingResponse(event_generator(), media_type="text/event-stream")
#
#
# @app.get("/ws", summary="描述 websocket 收发信息结构")
# async def ws(): ...
#
#
# @app.websocket("/ws")
# async def websocket_endpoint(
#         websocket: WebSocket, redis: Redis = Depends(get_async_redis)
# ):
#     await websocket.accept()
#
#     channel = BaseRedisChannel(redis=redis)
#
#     async def receive_from_websocket():
#         try:
#             while websocket.client_state == WebSocketState.CONNECTED:
#                 message = await websocket.receive_text()
#                 logger.info(f"receive: {message}")
#                 await channel.publish(message)
#                 update_state(message)
#         except WebSocketDisconnect:
#             logger.info("disconnect wb")
#
#     async def send_to_websocket():
#         try:
#             async for message in channel.listen():
#                 if websocket.client_state != WebSocketState.CONNECTED:
#                     break
#                 await websocket.send_text(message)
#         except WebSocketDisconnect:
#             logger.info("disconnect wb")
#
#     await asyncio.gather(receive_from_websocket(), send_to_websocket())
#
#     logger.info("disconnect wb")
#     await websocket.close()
#
#
# @app.get("/add/{num}")
# async def add_number(num: int, redis: Redis = Depends(get_async_redis)):
#     await BaseRedisChannel(redis=redis).publish(str(num))
#     update_state(num)
#     return "ok\n"

router = APIRouter(tags=['sandbox'])


@router.post('/sandbox', summary='导入地图创建沙盒实例')
async def sandbox_create():
    ...


@router.get('/sandbox', summary='获取沙盒实例信息')
async def sandbox_get():
    ...


@router.delete('/sandbox', summary='删除沙盒实例')
async def sandbox_delete():
    ...


@router.post('/sandbox/reset', summary='重置实例')
async def sandbox_reset():
    ...


@router.post('/sandbox/start', summary='开始运行沙盒')
async def sandbox_start():
    ...


@router.post('/sandbox/pause', summary='暂停运行沙盒')
async def sandbox_pause_start():
    ...


@router.post('/sandbox/replay', summary='运行回放')
async def sandbox_reset():
    ...


@router.post('/sandbox/npc/create', summary='增加机器人')
async def sandbox_npc_create():
    ...


@router.post('/sandbox/player/create', summary='增加玩家')
async def sandbox_player_create():
    ...

ws_router = APIRouter(tags=['ws(仅展示数据结构用)'])


@ws_router.get('/ws', summary='websocket')
async def get_ws():
    ...

app.include_router(router)
app.include_router(ws_router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)

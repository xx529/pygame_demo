import asyncio
import random
import uuid
from asyncio import Queue
from enum import Enum
from typing import List, Literal

from faker import Faker
from langchain_openai import ChatOpenAI
from loguru._logger import Logger
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from logger import get_logger

logger = get_logger()


class RunningState(str, Enum):
    RUNNING = 'running'
    STOPPED = 'stoped'


class BaseSimulator(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str = Field(description='模拟器名称')
    api_key: str = Field(description='key')
    api_base: str = Field(description='url')
    llm_model: str = Field(description='模型名称')
    running_state: RunningState = Field(RunningState.RUNNING, description='运行状态')

    _logger: Logger | None = PrivateAttr(None)
    _llm: ChatOpenAI | None = PrivateAttr(None)

    @property
    def logger(self):
        if self._logger is None:
            self._logger = get_logger(self.name)
        return self._logger

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOpenAI(api_key=self.api_key, base_url=self.api_base, model_nae=self.llm_modelm)
        return self._llm


class Event(BaseModel):
    ...


class ContentEvent(Event):
    content: str = Field('', description='内容')


class StateEvent(Event):
    state: RunningState = Field('', description='运行状态')


class CharacterSimulator(BaseSimulator):
    id: str = Field(uuid.uuid4().hex, description='character id')
    name: str = Field(description='人物名称')
    events: Queue = Field(default_factory=Queue, description='事件队列')

    async def run(self):
        while True:
            event = await self.events.get()
            match event:
                case StateEvent():
                    self.logger.info(f'chang state: {event}')
                    self.running_state = event.state
                case ContentEvent():
                    if self.running_state == RunningState.STOPPED:
                        continue
                    self.logger.info(event)

            await asyncio.sleep(random.randint(1, 5))


class EnvironmentSimulator(BaseSimulator):
    name: Literal['env'] = Field('env', description='名称')
    characters: List[CharacterSimulator] = Field(default_factory=list, description='人物模拟器')

    async def add_character(self, character: CharacterSimulator):
        if self.is_available:
            self.characters.append(character)
            asyncio.create_task(character.run())

    async def add_event(self, event: Event):
        if self.is_available:
            for c in self.characters:
                await c.events.put(event)

    async def stop(self):
        self.running_state = RunningState.STOPPED
        await self.add_event(StateEvent(state=RunningState.STOPPED))

    @property
    def is_available(self):
        if self.running_state == RunningState.RUNNING:
            return True
        else:
            return False


async def main():
    fake = Faker()

    env = EnvironmentSimulator()

    c1 = CharacterSimulator(name='alice')
    c2 = CharacterSimulator(name='bob')

    c2.running_state = RunningState.STOPPED

    await env.add_character(c1)
    await env.add_character(c2)

    for i in range(10):
        await env.add_character(CharacterSimulator(name=fake.name()))
        num = str(random.randint(1, 100))
        await env.add_event(ContentEvent(content=num))
        logger.info(f'{i}-{num}-{"-"*20}')
        await asyncio.sleep(1)

    await env.stop()

    await asyncio.sleep(100)


if __name__ == '__main__':
    asyncio.run(main())

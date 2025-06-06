import json
import uuid
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Weather(str, Enum):
    SUNNY = 'sunny'
    RAINY = 'rainy'


class TimeOfDay(str, Enum):
    MORNING = 'morning'
    AFTERNOON = 'afternoon'
    EVENING = 'evening'
    MIDNIGHT = 'midnight'


class Environment(BaseModel):
    weather: Weather = Field(Weather.SUNNY, description='当前天气')
    time_of_day: TimeOfDay = Field(TimeOfDay.MORNING, description='时间段')


class Position(BaseModel):
    x: int = Field(description='网格坐标 x')
    y: int = Field(description='网格坐标 y')


class Npc(BaseModel):
    id: str = Field(description='npc id')
    name: str = Field(description='npc 名称')
    pos: Position = Field(description='npc 位置')
    attrs: dict = Field(description='player 属性')


class Grid(BaseModel):
    name: str = Field('grid', description='网格名称')
    grid: List[List[int]] = Field(description='网格标记')


class Map(BaseModel):
    width: int = Field(description='网格宽')
    height: int = Field(description='网格高')
    areas: List[Grid] = Field(description='地区区域信息')
    collision: Grid = Field(description='碰撞区域')


class Player(BaseModel):
    id: str = Field(description='player id')
    name: str = Field(description='player 名称')
    pos: Position = Field(description='player 位置')
    attrs: dict = Field(description='player 属性')


class GameInstanceState(BaseModel):
    id: str = Field(description='实例ID')
    version: str = Field(description='版本号')
    name: str = Field(description="实例名称")
    start_at: datetime = Field(description='开始时间')
    duration: int = Field(description='已运行时长')
    environment: Environment = Field(description='世界环境')
    map: Map = Field(description='地图信息')
    npcs: List[Npc] = Field(description='npc 列表')
    players: List[Player] = Field(description='player 列表')

    @classmethod
    def json_schema_data(cls):
        return json.dumps(obj={'type': 'object', 'title': cls.__name__,
                               'properties': GameInstanceState.model_json_schema()['properties']}, ensure_ascii=False)


g = GameInstanceState(
    id=uuid.uuid4().hex,
    version='1.0.0',
    name="test",
    start_at=datetime.now(),
    environment=Environment(
        weather=Weather.SUNNY,
        time_of_day=TimeOfDay.MORNING,
    ),
    map=Map(
        width=3,
        height=3,
        areas=[
            Grid(name='地方1', grid=[[1, 1, 1], [0, 0, 0], [0, 0, 0]]),
            Grid(name='地方2', grid=[[1, 1, 1], [1, 1, 1], [0, 0, 0]]),
        ],
        collision=Grid(name='collision', grid=[[0, 0, 0], [0, 0, 0], [1, 1, 1]])
    ),
    npcs=[
        Npc(id=uuid.uuid4().hex, name='npc1', pos=Position(x=0, y=1))
    ],
    players=[
        Player(id=uuid.uuid4().hex, name='npc1', pos=Position(x=1, y=1))
    ]
)

print(g.model_dump_json(indent=2))

print(GameInstanceState.json_schema_data())

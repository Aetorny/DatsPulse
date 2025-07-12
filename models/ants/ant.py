from dataclasses import dataclass
from models.ants.state_type import StateType
from models.food import Food
from models.vector2 import Vector2
from typing import ClassVar
from models.ants.ant_type import AntType


@dataclass
class Ant:
    MAX_HEALTH: ClassVar[int]
    ATTACK: ClassVar[int]
    CAPACITY: ClassVar[int] # грузоподъемность
    VISION: ClassVar[int] # обзор
    SPEED: ClassVar[int]

    id: str
    q: int # столбец
    r: int # строка
    health: int
    food: Food | None
    type: AntType
    state: StateType = StateType.SEARCH

    @staticmethod
    def from_dict(data: dict) -> 'Ant':
        return Ant(
            id=data['id'],
            q=data['q'],
            r=data['r'],
            health=data['health'],
            type = AntType(data["type"]),
            food=None if data['food']['amount'] == 0 else Food.from_dict(data['food'] | {'r': 0, 'q': 0
            })
        )

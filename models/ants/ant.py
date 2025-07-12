from typing import Any, ClassVar

from dataclasses import dataclass
from models.ants.state_type import StateType
from models.food import Food
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
    food: Food
    type: AntType
    state: StateType = StateType.SEARCH

    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'Ant':
        return Ant(
            id=data['id'],
            q=data['q'],
            r=data['r'],
            health=data['health'],
            type = AntType(data["type"]),
            food=Food.from_dict(data['food'] | {'r': 0, 'q': 0})
        )

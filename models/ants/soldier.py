from typing import Any
from models.ants.ant import Ant
from models.ants.ant_type import AntType
from models.food import Food


class SoldierAnt(Ant):
    MAX_HEALTH: int = 180
    ATTACK: int = 70
    CAPACITY: int = 2 # грузоподъемность
    VISION: int = 1 # обзор
    SPEED: int = 4

    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'SoldierAnt':
        return SoldierAnt(
            id=data['id'],
            q=data['q'],
            r=data['r'],
            health=data['health'],
            type = AntType(data["type"]),
            food=Food.from_dict(data['food'] | {'r': 0, 'q': 0})
        )
from typing import Any
from models.ants.ant import Ant
from models.ants.ant_type import AntType
from models.food import Food


class ScoutAnt(Ant):
    MAX_HEALTH: int = 80
    ATTACK: int = 20
    CAPACITY: int = 2 # грузоподъемность
    VISION: int = 4 # обзор
    SPEED: int = 7

    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'ScoutAnt':
        return ScoutAnt(
            id=data['id'],
            q=data['q'],
            r=data['r'],
            health=data['health'],
            type = AntType(data["type"]),
            food=Food.from_dict(data['food'] | {'r': 0, 'q': 0})
        )
from typing import Any
from models.ants.ant import Ant
from models.ants.ant_type import AntType
from models.food import Food


class WorkerAnt(Ant):
    MAX_HEALTH: int = 130
    ATTACK: int = 30
    CAPACITY: int = 8 # грузоподъемность
    VISION: int = 1 # обзор
    SPEED: int = 5

    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'WorkerAnt':
        return WorkerAnt(
            id=data['id'],
            q=data['q'],
            r=data['r'],
            health=data['health'],
            type = AntType(data["type"]),
            food=Food.from_dict(data['food'] | {'r': 0, 'q': 0})
        )
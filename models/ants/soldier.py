from models.ants.ant import Ant


class SoldierAnt(Ant):
    MAX_HEALTH: int = 180
    ATTACK: int = 70
    CAPACITY: int = 2 # грузоподъемность
    VISION: int = 1 # обзор
    SPEED: int = 4

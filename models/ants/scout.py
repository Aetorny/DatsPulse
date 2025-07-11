from models.ants.ant import Ant


class ScoutAnt(Ant):
    MAX_HEALTH: int = 80
    ATTACK: int = 20
    CAPACITY: int = 2 # грузоподъемность
    VISION: int = 4 # обзор
    SPEED: int = 7

from models.ants.ant import Ant


class WorkerAnt(Ant):
    MAX_HEALTH: int = 130
    ATTACK: int = 30
    CAPACITY: int = 8 # грузоподъемность
    VISION: int = 1 # обзор
    SPEED: int = 5

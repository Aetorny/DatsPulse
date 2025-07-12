from enum import Enum

class StateType(Enum):
    SEARCH = 0
    GOTO_FOOD = 1
    GOTO_BASE = 2
    PENDING = 3


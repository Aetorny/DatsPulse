from typing import Any, Literal


class Ant:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @property
    def food(self) -> dict[Literal['amount', 'type'], int]:
        return {
            'amount': self.data['food']['amount'],
            'type': self.data['food']['type']
        }
    
    @property
    def health(self) -> int:
        return self.data['health']

    @property
    def id(self) -> str:
        return self.data['id']
    
    @property
    def lastEnemyAnt(self) -> str:
        return self.data['lastEnemyAnt']

    @property
    def lastMove(self) -> list[dict[Literal['q', 'r'], int]]:
        return self.data['lastMove']

    @property
    def move(self) -> list[dict[Literal['q', 'r'], int]]:
        return self.data['move']

    @property
    def q(self) -> int:
        return self.data['q']

    @property
    def r(self) -> int:
        return self.data['r']

    @property
    def type(self) -> str:
        return self.data['type']
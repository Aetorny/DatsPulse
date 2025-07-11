from ant import Ant
from typing import Any

class Squad:
    def __init__(self, x: int, y: int):
        self.ants: list[Ant] = []
        self.x: int = x # позиция, от которой будут вычисляться позиции остальных муравьев 
        self.y: int = y

    def add(self, ant: Ant):
        self.ants.append(ant)

    def move_to(self, x: int, y: int) -> list[dict[str, Any]]:
        moves = []
        self.x = x
        self.y = y

        idx = 0
        for ant in self.ants:
            moves.append({ant.id: 
                          [
                              {"q": x + idx // int(len(self.ants)**0.5),
                               "r": y + idx %  int(len(self.ants)**0.5)}
                          ]
                          })
            idx += 1

        print(moves)

        return moves

if __name__ == "__main__":
    # дебаг

    s = Squad(0, 0)
    for i in range(1):
        s.add(Ant({"id": "bob"}))
    
    s.move_to(2, 3)

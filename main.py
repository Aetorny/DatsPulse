from typing import Any, Literal
import requests

from ant import Ant

URL = 'https://games-test.datsteam.dev/api/'
HEADERS = {
    "accept": "application/json",
    "X-Auth-Token": "b12a46bf-db96-4d30-9add-72d1184e05d3"
}


class App:
    def __init__(self) -> None:
        self.scouts: list[Ant] = []
        self.soldiers: list[Ant] = []
        self.workers: list[Ant] = []
        self.turnNo = -1

    def get_distance(self, q1: int, r1: int, q2: int, r2: int) -> int:
        x1 = q1 - (r1 - (r1 & 1)) // 2
        z1 = r1
        y1 = -x1 - z1

        x2 = q2 - (r2 - (r2 & 1)) // 2
        z2 = r2
        y2 = -x2 - z2

        distance = max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))

        return distance

    def add_new_squad(self) -> None: # TODO
        ...

    def new_turn(self) -> None:
        self.scouts: list[Ant] = []
        self.soldiers: list[Ant] = []
        self.workers: list[Ant] = []
        for ant in self.ants:
            type_ = ant['type']
            if type_ == 'scout':
                self.scouts.append(Ant(ant))
            elif type_ == 'soldier':
                self.soldiers.append(Ant(ant))
            elif type_ == 'worker':
                self.workers.append(Ant(ant))
            

    def get_arena(self) -> None:
        response = requests.get(URL+'arena', headers=HEADERS)

        data: dict[str, Any] = response.json()
        if data.get('error', None):
            return print(data)

        import json
        with open('test2.json', 'w') as f:
            json.dump(data, f, indent=4)

        # Список ваших юнитов
        self.ants: list[dict[str, Any]] = data['ants']

        # Видимые враги
        self.enemies: list[dict[str, Any]] = data['enemies']

        # Видимые ресурсы
        self.food: list[dict[str, Any]] = data['food']

        # Координаты вашего муравейника
        self.home: list[dict[str, Any]] = data['home']

        # Видимые гексы карты
        self.map: list[dict[str, Any]] = data['map']

        self.nextTurnIn: int = data['nextTurnIn'] # Количество секунд до следующего хода
        self.score: int = data['score'] # Текущий счёт команды
        self.spot: dict[Literal['q', 'r'], int] = data['spot'] # Координаты основного гекса муравейника
        if data['turnNo'] != self.turnNo:
            self.turnNo = data['turnNo'] # Номер текущего хода
            self.new_turn()

    def move_all_ants(self) -> None:
        moves = []
        path1 = [
            {
                "q": self.spot['q']+1,
                "r": self.spot['r']
            },
            {
                "q": self.spot['q']+2,
                "r": self.spot['r']
            },
            {
                "q": self.spot['q']+2,
                "r": self.spot['r']+1
            },
            {
                "q": self.spot['q']+2,
                "r": self.spot['r']+2
            }
        ]
        path2 = [
            {
                "q": self.spot['q']+1,
                "r": self.spot['r']+2
            },
            {
                "q": self.spot['q'],
                "r": self.spot['r']+2
            },
            {
                "q": self.spot['q'],
                "r": self.spot['r']+1
            },
            {
                "q": self.spot['q'],
                "r": self.spot['r']
            }
        ]
        for ant in self.ants:
            moves.append({
                "ant": ant['id'],
                "path": path1 if ant['q'] != self.spot['q'] else path2
            })

        self.post_move(moves)

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        requests.post(URL+'move', headers=HEADERS, json=data).json()

    def register(self) -> None:
        print(requests.post(URL+'register', headers=HEADERS).json())


def main() -> None:
    app = App()
    # app.register()
    # import time
    # while True:
    #     time.sleep(1)
    #     app.get_arena()
    #     app.move_all_ants()


if __name__ == '__main__':
    main()
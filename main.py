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
        self.squads: list[dict[str, Ant]] = []
        self.ants_to_squad: dict[str, int] = {}
        self.turnNo = -1

    def add_new_squad(self) -> None: # TODO
        ...

    def new_turn(self) -> None:
        for ant in self.ants:
            id_ = ant['id']
            if id_ in self.ants_to_squad:
                self.squads[self.ants_to_squad[id_]][id_] = Ant(ant)
            else:
                self.add_new_squad()

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
        for ant in self.ants:
            moves.append({
                "ant": ant['id'],
                "path": [
                    {
                        "q": ant['q']-1,
                        "r": ant['r']
                    }
                ]
            })
            if ant['food']['amount'] > 0:
                moves[-1]['path'][-1]['q'] += 2

        self.post_move(moves)

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        _response = requests.post(URL+'move', headers=HEADERS, json=data)

    def register(self) -> None:
        print(requests.post(URL+'register', headers=HEADERS).json())


def main() -> None:
    app = App()
    app.register()
    # import time
    # while True:
    #     time.sleep(1)
    #     app.get_arena()
    #     app.move_all_ants()


if __name__ == '__main__':
    main()
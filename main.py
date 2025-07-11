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
        self.scouts: dict[str, Ant] = {}
        self.soldiers: dict[str, Ant] = {}
        self.builders: dict[str, Ant] = {}
        self.turnNo = -1

    def new_turn(self) -> None:
        ...
        # for ant in self.ants:
        #     if ant['type'] == 2:
        #         self.scouts.append(Ant(ant))
        #     elif ant['type'] == 1:
        #         self.soldiers.append(Ant(ant))
        #     elif ant['type'] == 0:
        #         self.builders.append(Ant(ant))

    def get_arena(self) -> None:
        response = requests.get(URL+'arena', headers=HEADERS)

        data: dict[str, Any] = response.json()
        if data.get('error', None):
            return print(data)
        import json
        with open('test.json', 'w') as f:
            json.dump(data, f, indent=4)
        print(data)
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

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        _response = requests.post(URL+'move', headers=HEADERS, json=data)


def main() -> None:
    app = App()
    app.get_arena()


if __name__ == '__main__':
    main()
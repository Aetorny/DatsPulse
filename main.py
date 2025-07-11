from typing import Any, Literal
import requests

URL = 'https://games-test.datsteam.dev/api/'
HEADERS = {
    "accept": "application/json",
    "X-Auth-Token": "b12a46bf-db96-4d30-9add-72d1184e05d3"
}


class App:
    def __init__(self) -> None:
        pass

    def get_arena(self) -> None:
        response = requests.get(URL+'arena', headers=HEADERS)

        data = response.json()
        if data['error']:
            return print(data)

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
        self.turnNo = data['turnNo'] # Номер текущего хода

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        _response = requests.post(URL+'move', headers=HEADERS, json=data)


def main() -> None:
    app = App()


if __name__ == '__main__':
    main()
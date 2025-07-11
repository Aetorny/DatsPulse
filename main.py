from typing import Any, Literal
import requests
import time
import random

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
        self.worker = None

    def get_hex_path_odd_r(self,
        col1: int, row1: int, col2: int, row2: int
    ) -> list[tuple[int, int]]:
        def oddr_to_cube(col: int, row: int) -> tuple[int, int, int]:
            x = col - (row - (row & 1)) // 2
            z = row
            y = -x - z
            return (x, y, z)

        def cube_to_oddr(x: int, y: int, z: int) -> tuple[int, int]:
            row = z
            col = x + (z - (z & 1)) // 2
            return (col, row)

        def cube_lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[float, float, float]:
            return (
                a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t,
            )

        def cube_round(x: float, y: float, z: float) -> tuple[int, int, int]:
            rx, ry, rz = round(x), round(y), round(z)
            dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)

            if dx > dy and dx > dz:
                rx = -ry - rz
            elif dy > dz:
                ry = -rx - rz
            else:
                rz = -rx - ry
            return (rx, ry, rz)

        a = oddr_to_cube(col1, row1)
        b = oddr_to_cube(col2, row2)
        N = max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))

        path = []
        if N == 0:
            return []
        for i in range(N + 1):
            t = i / N
            interpolated = cube_lerp(a, b, t)
            rounded = cube_round(*interpolated)
            col, row = cube_to_oddr(*rounded)
            path.append((col, row))

        return path


    def get_distance(self, q1: int, r1: int, q2: int, r2: int) -> int:
        assert isinstance(q1, int) and isinstance(r1, int) and isinstance(q2, int) and isinstance(r2, int), 'q and r must be int'
        x1 = q1 - (r1 - (r1 & 1)) // 2
        z1 = r1
        y1 = -x1 - z1

        x2 = q2 - (r2 - (r2 & 1)) // 2
        z2 = r2
        y2 = -x2 - z2

        distance = max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))

        return distance

    def go_to_food(self) -> None:
        moves = []
        # for worker in self.workers:
        worker = self.worker
        if worker.food['amount'] == 0:
            closest_food = min([food for food in self.food if food['type'] != 3], key=lambda f: self.get_distance(worker.q, worker.r, f['q'], f['r']))
            path = self.get_hex_path_odd_r(worker.q, worker.r, closest_food['q'], closest_food['r'])
        else:
            h = max(self.home, key=lambda h:(h['q'], h['r']))
            if h == self.spot:
                h = min(self.home, key=lambda h:(h['q'], h['r']))
            path = self.get_hex_path_odd_r(worker.q, worker.r, h['q'], h['r'])
        print(path, worker.q, worker.r)
        if len(path) == 0:
            return print('no path', closest_food)
        if path[0] == (worker.q, worker.r):
            path = path[1:]
        if len(path) > 4:
            path = path[:4]
        if path[0] == (self.spot['q'], self.spot['r']):
            one = random.randint(0, 1)
            path = self.get_hex_path_odd_r(worker.q, worker.r, self.spot[0]+one, self.spot[1]+one)
        moves.append({
            'ant': worker.id,
            'path': [
                {
                    'q': path[i][0],
                    'r': path[i][1]
                } for i in range(len(path))
            ]
        })
        print(path)
        self.post_move(moves)

    def new_turn(self) -> None:
        self.scouts: list[Ant] = []
        self.soldiers: list[Ant] = []
        self.workers: list[Ant] = []
        for ant in self.ants:
            type_ = ant['type']
            if type_ == 2:
                self.scouts.append(Ant(ant))
            elif type_ == 1:
                self.soldiers.append(Ant(ant))
            elif type_ == 0:
                self.workers.append(Ant(ant))
        if self.worker is None:
            self.worker = self.workers[0]
            self.id = self.worker.id
            print(self.worker, self.worker.id)
        for worker in self.workers:
            if worker.id == self.id:
                self.worker = worker
        self.go_to_food()

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

        if len(self.map) == 0:
            return

        self.nextTurnIn: int = data['nextTurnIn'] # Количество секунд до следующего хода
        self.score: int = data['score'] # Текущий счёт команды
        self.spot: dict[Literal['q', 'r'], int] = data['spot'] # Координаты основного гекса муравейника
        if data['turnNo'] != self.turnNo:
            self.turnNo = data['turnNo'] # Номер текущего хода
            self.new_turn()
        
        time.sleep(self.nextTurnIn)

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        requests.post(URL+'move', headers=HEADERS, json=data).json()

    def register(self) -> None:
        print(requests.post(URL+'register', headers=HEADERS).json())


def main() -> None:
    app = App()
    # print(app.get_hex_path_odd_r(3, 6, 4, 5))
    app.register()

    while True:
        app.get_arena()


if __name__ == '__main__':
    main()
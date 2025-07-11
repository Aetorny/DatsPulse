from typing import Any, Literal, Optional
import requests
import time

from ant import Ant

URL = 'https://games-test.datsteam.dev/api/'
HEADERS = {
    "accept": "application/json",
    "X-Auth-Token": "b12a46bf-db96-4d30-9add-72d1184e05d3"
}

def cube_to_oddr(x: int, y: int, z: int) -> tuple[int, int]:
    row = z
    col = x + (z - (z & 1)) // 2
    return (col, row)

def oddr_to_cube(col: int, row: int) -> tuple[int, int, int]:
     x = col - (row - (row & 1)) // 2
     z = row
     y = -x - z
     return (x, y, z)

def cube_add(a : tuple[int, int, int], b : tuple[int, int, int]) -> tuple[int, ...]:
    return tuple([sum(i) for i in zip(a, b)])


def neighbors(q: int, r: int) -> list[tuple[int, int]]:
    coords = oddr_to_cube(q, r)
    output: list[tuple[int, int]] = []
    for offset in [(1, 0, -1), (1, -1, 0), (0, -1, 1), (-1, 0, 1), (-1, 1, 0), (0, 1, -1)]:
       t = cube_add(coords, offset) 
       output.append(cube_to_oddr(t[0], t[1], t[2]))
    return output

def cube_spiral(c : tuple[int, int], radius: int) -> list[tuple[int, int]]:
    output = [c]

    for k in range(1, radius+1):
        hex = cube_add(oddr_to_cube(c[0], c[1]), (-k, k, 0))
        base_tile = hex
        for i in range(6):
            for _ in range(k):
                output.append(cube_to_oddr(hex[0], hex[1], hex[2]))
                t = neighbors(output[-1][0], output[-1][1])[i]
                hex = oddr_to_cube(t[0], t[1])

        output.append(cube_to_oddr(base_tile[0], base_tile[1], base_tile[2]))
    
    return output


class App:
    def __init__(self) -> None:
        self.scouts: list[Ant] = []

        self.soldiers: list[Ant] = []
        self.soldiers_positions: set[tuple[int, int]] = set()
        self.cells_around_base: Optional[set[tuple[int, int]]] = None
        self.workers: list[Ant] = []
        self.moves: list[dict[str, Any]] = []
        self.turnNo = -1
        self.home_cell_1: Optional[tuple[int, int]] = None
        self.home_cell_2: Optional[tuple[int, int]] = None

    def get_hex_path_odd_r(self,
        col1: int, row1: int, col2: int, row2: int
    ) -> list[tuple[int, int]]:

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

        path: list[tuple[int, int]] = []
        if N == 0:
            return []
        for i in range(N + 1):
            t = i / N
            interpolated = cube_lerp(a, b, t)
            rounded = cube_round(*interpolated)
            col, row = cube_to_oddr(*rounded)
            path.append((col, row))

        return self.filter_path(path)

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

    def get_cells_around(self, col: int, row: int) -> list[tuple[int, int]]:
        cells = [(col, row-1), (col, row+1), (col-1, row), (col+1, row)]
        if row % 2 == 0:
            temp_col = col - 1
        else:
            temp_col = col + 1
        cells.append((temp_col, row-1))
        cells.append((temp_col, row+1))
        return cells

    def move_soldiers_to_guard(self) -> None:
        if len(self.soldiers) == 0:
            return
        assert self.cells_around_base, 'cells_around_base must not be None'

        soldier = None
        for soldier in self.soldiers:
            if soldier.q == self.spot['q'] and soldier.r == self.spot['r']:
                break
        
        empty_cells = list(self.cells_around_base.difference(self.soldiers_positions))
        assert len(empty_cells) > 0, 'empty_cells must not be empty'
        assert isinstance(soldier, Ant), 'soldier must be Ant'

        empty_cells.sort(key=lambda cell: self.get_distance(soldier.q, soldier.r, cell[0], cell[1]))

        for cell in empty_cells:
            if self.get_distance(soldier.q, soldier.r, cell[0], cell[1]) == 1:
                self.moves.append({
                    'ant': soldier.id,
                    'path': [{
                        'q': cell[0],
                        'r': cell[1]
                    }]
                })
                self.soldiers_positions.add((cell[0], cell[1]))
                return
            elif self.get_distance(soldier.q, soldier.r, cell[0], cell[1]) == 2:
                for home_cell in self.home:
                    if home_cell == self.spot:
                        continue
                    if self.get_distance(cell[0], cell[1], home_cell['q'], home_cell['r']) == 1 \
                        and self.get_distance(soldier.q, soldier.r, home_cell['q'], home_cell['r']) == 1:
                        self.moves.append({
                            'ant': soldier.id,
                            'path': [{
                                'q': home_cell['q'],
                                'r': home_cell['r']
                            }, {
                                'q': cell[0],
                                'r': cell[1]
                            }]
                        })
                        self.soldiers_positions.add((cell[0], cell[1]))
                        return
            else:
                cell1, cell2 = [cell for cell in self.home if cell != self.spot]
                if self.get_distance(soldier.q, soldier.r, cell1['q'], cell1['r']) == 2:
                    cell1, cell2 = cell2, cell1
                self.moves.append({
                    'ant': soldier.id,
                    'path': [{
                        'q': cell1['q'],
                        'r': cell1['r']
                    }, {
                        'q': cell2['q'],
                        'r': cell2['r']
                    }, {
                        'q': cell[0],
                        'r': cell[1]
                    }]
                })
                self.soldiers_positions.add((cell[0], cell[1]))
                return

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


        assert self.cells_around_base, 'cells_around_base must not be None'
        if len(self.soldiers)-1 < len(self.cells_around_base):
            self.move_soldiers_to_guard()

        self.prepare_map()

    def get_arena(self) -> None:
        self.moves = []
        response = requests.get(URL+'arena', headers=HEADERS)

        data: dict[str, Any] = response.json()
        if data.get('error', None):
            return print(data)

        import json
        with open('test2.json', 'w') as f:
            json.dump(data, f, indent=4)

        # Список ваших юнитов
        self.ants: list[dict[str, Any]] = data['ants']
        if len(self.ants) == 0:
            time.sleep(1)
            return

        # Видимые враги
        self.enemies: list[dict[str, Any]] = data['enemies']

        # Позиции врагов и наших живчиков (разведчиков и работников)
        self.units_poses : set[tuple[int, int]] = set()

        # Видимые ресурсы
        self.food: list[dict[str, Any]] = data['food']

        # Координаты вашего муравейника
        self.home: list[dict[str, Any]] = data['home']
        if self.cells_around_base is None:
            cells: list[tuple[int, int]] = []
            for cell in self.home:
                cells += self.get_cells_around(cell['q'], cell['r'])
            temp = set(cells)
            for cell in self.home:
                temp.remove((cell['q'], cell['r']))
            self.cells_around_base = temp

        # Видимые гексы карты
        self.map: list[dict[str, Any]] = data['map']
        self.prep_map: dict[tuple[int, int], dict[str, Any]] = {}

        self.nextTurnIn: int = data['nextTurnIn'] # Количество секунд до следующего хода
        self.score: int = data['score'] # Текущий счёт команды
        self.spot: dict[Literal['q', 'r'], int] = data['spot'] # Координаты основного гекса муравейника
        if self.home_cell_1 is None or self.home_cell_2 is None:
            cell1, cell2 = [cell for cell in self.home if cell != self.spot]
            self.home_cell_1 = (cell1['q'], cell1['r'])
            self.home_cell_2 = (cell2['q'], cell2['r'])

        if data['turnNo'] != self.turnNo:
            self.turnNo = data['turnNo'] # Номер текущего хода
            self.new_turn()

        self.post_move(self.moves)

    def prepare_map(self) -> None:
        for tile in self.map:
            self.prep_map[(tile["q"], tile["r"])] = tile

        for ant in self.ants:
            self.units_poses.add((ant["q"], ant["r"]))

        for enemy in self.enemies:
            self.units_poses.add((enemy["q"], enemy["r"]))

    def bad_tile(self, i : tuple[int, int]) -> bool:
        return self.prep_map[i]["type"] == 5 or \
               i in self.units_poses

    def pathcost(self, path: list[tuple[int, int]]) -> int:
        i = 0
        for tile in path:
            i += self.prep_map[tile]["cost"]
        return i

    def filter_path(self, path: list[tuple[int, int]]) -> list[tuple[int, int]]:
        output = path.copy()
        for i in range(1, len(output) - 1):
            if self.bad_tile(output[i]):
                n = neighbors(output[i][0], output[i][1]) 
                a, b = n.index(output[i-1]), n.index(output[i+1])

                if a > b:
                    a, b = b, a
                    n = n[::-1]

                path1 = n[a+1:b]
                path2 = n[a+1:-1] + n[:b:-1]

                path = path1 if self.pathcost(path1) < self.pathcost(path2) else path2

                output = output[:i] + path + output[i+1:]

        return output[1:]

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        data = {
            "moves": moves
        }

        data = requests.post(URL+'move', headers=HEADERS, json=data).json()

        self.nextTurnIn: int = data['nextTurnIn']

        time.sleep(self.nextTurnIn)


    def register(self) -> None:
        print(requests.post(URL+'register', headers=HEADERS).json())

    def scout_movement(self) -> None:
        


def main() -> None:
    app = App()
    # print(app.get_hex_path_odd_r(3, 6, 4, 5))
    app.register()

    while True:
        app.get_arena()


if __name__ == '__main__':
    print(cube_spiral((3, 3), 4))
    # main()

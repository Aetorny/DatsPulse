from typing import Any, Literal, Optional
import requests
import time

from models.ants.ant import Ant
from models.ants.ant_type import AntType
from models.ants.state_type import StateType
from models.map import Map
from models.food import Food
from models.vector2 import Vector2

from models.ants.soldier import SoldierAnt
from models.ants.scout import ScoutAnt
from models.ants.worker import WorkerAnt
from models.hex_type import HexType

import json


from transformer import DataTransformer

URL = 'https://games-test.datsteam.dev/api/'
HEADERS = {
    "accept": "application/json",
    "X-Auth-Token": "b12a46bf-db96-4d30-9add-72d1184e05d3"
}

def cube_to_oddr(x: int, y: int, z: int) -> Vector2:
    row = z
    col = x + (z - (z & 1)) // 2
    return Vector2(col, row)

def oddr_to_cube(col: int, row: int) -> tuple[int, int, int]:
     x = col - (row - (row & 1)) // 2
     z = row
     y = -x - z
     return (x, y, z)

def neighbors(q: int, r: int) -> list[Vector2]:
    coords = oddr_to_cube(q, r)
    output: list[Vector2] = []
    for offset in [(1, 0, -1), (1, -1, 0), (0, -1, 1), (-1, 0, 1), (-1, 1, 0), (0, 1, -1)]:
        output.append(cube_to_oddr(
            coords[0]+offset[0], coords[1]+offset[1], coords[2]+offset[2],))
    return output

def cube_add(a : tuple[int, int, int], b : tuple[int, int, int]) -> tuple[int, ...]:
    return tuple([sum(i) for i in zip(a, b)])

def cube_spiral(c : Vector2, radius: int, span: int) -> list[Vector2]:
    output = [c]

    for k in range(1, radius+1):
        hex = cube_add(oddr_to_cube(c.q, c.r), (-k, k, 0))
        base_tile = hex

        if k % (2*span+1) == 0:
            for i in range(6):
                for _ in range(k):
                    output.append(cube_to_oddr(hex[0], hex[1], hex[2]))
                    t = neighbors(output[-1].q, output[-1].r)[i]
                    hex = oddr_to_cube(t.q, t.r)

        output.append(cube_to_oddr(base_tile[0], base_tile[1], base_tile[2]))
    
    return output


class App:
    def __init__(self) -> None:
        self.scouts: list[Ant] = []
        self.soldiers: list[Ant] = []
        self.soldiers_positions: set[Vector2] = set()
        self.cells_around_base: Optional[set[Vector2]] = None
        self.workers: list[Ant] = []
        self.moves: list[dict[str, Any]] = []
        self.turnNo = -1
        self.house_cell_1: Optional[Vector2] = None
        self.house_cell_2: Optional[Vector2] = None 

    def get_hex_path_odd_r(self,
        col1: int, row1: int, col2: int, row2: int
    ) -> list[Vector2]:

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

        path: list[Vector2] = []
        if N == 0:
            return []
        for i in range(N + 1):
            t = i / N
            interpolated = cube_lerp(a, b, t)
            rounded = cube_round(*interpolated)
            col, row = cube_to_oddr(*rounded)
            path.append(Vector2(col, row))

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

    def get_cells_around(self, col: int, row: int) -> list[Vector2]:
        cells = [Vector2(col, row-1), Vector2(col, row+1), Vector2(col-1, row), Vector2(col+1, row)]
        if row % 2 == 0:
            temp_col = col - 1
        else:
            temp_col = col + 1
        cells.append(Vector2(temp_col, row-1))
        cells.append(Vector2(temp_col, row+1))
        return cells

    def move_soldiers_to_guard(self) -> None:
        # проверка на наличие солдатов
        if len(self.soldiers) == 0:
            return
        assert self.cells_around_base, 'cells_around_base must not be None'

        # пытаемся найти солдата, который заспавнился в муравейнике
        soldier = None
        for soldier in self.soldiers:
            if soldier.q == self.spot_house.q and soldier.r == self.spot_house.r:
                break
        
        # получаем свободные клетки для размещения
        empty_cells = list(self.cells_around_base.difference(self.soldiers_positions))
        assert len(empty_cells) > 0, 'empty_cells must not be empty'
        assert isinstance(soldier, Ant), 'soldier must be Ant'

        # сортируем свободные клетки по близости (сначала - самые близкие)
        empty_cells.sort(key=lambda cell: self.get_distance(soldier.q, soldier.r, cell.q, cell.r))

        # строим маршрут до свободной клетки
        for cell in empty_cells:
            if self.get_distance(soldier.q, soldier.r, cell.q, cell.r) == 1:
                self.moves.append({
                    'ant': soldier.id,
                    'path': [{
                        'q': cell.q,
                        'r': cell.r
                    }]
                })
                return
            elif self.get_distance(soldier.q, soldier.r, cell.q, cell.r) == 2:
                for home_cell in self.houses:
                    if home_cell == self.spot_house:
                        continue
                    if self.get_distance(cell.q, cell.r, home_cell.q, home_cell.r) == 1 \
                        and self.get_distance(soldier.q, soldier.r, home_cell.q, home_cell.r) == 1:
                        self.moves.append({
                            'ant': soldier.id,
                            'path': [{
                                'q': home_cell.q,
                                'r': home_cell.r
                            }, {
                                'q': cell.q,
                                'r': cell.r
                            }]
                        })
                        return
            else:
                cell1, cell2 = [cell for cell in self.houses if cell != self.spot_house]
                if self.get_distance(soldier.q, soldier.r, cell1.q, cell1.r) == 2:
                    cell1, cell2 = cell2, cell1
                self.moves.append({
                    'ant': soldier.id,
                    'path': [{
                        'q': cell1.q,
                        'r': cell1.r
                    }, {
                        'q': cell2.q,
                        'r': cell2.r
                    }, {
                        'q': cell.q,
                        'r': cell.r
                    }]
                })

    def new_turn(self) -> None:
        '''
        Просчитывание нового хода
        '''
        assert self.cells_around_base, 'cells_around_base must not be None'
        if len(self.soldiers) - 1 < len(self.cells_around_base):
            self.move_soldiers_to_guard()
        self.worker_logic()
    
    def save_response(self, data: dict, filename: str = 'test.json'):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def get_arena(self) -> None:
        # обнуляем список ходов
        self.moves = []

        # получаем данные
        response = requests.get(URL + 'arena', headers=HEADERS)
        data: dict[str, Any] = response.json()
        if data.get('error', None):
            return print(data)

        # сохраняем response в файл
        self.save_response(data)

        # наши муравьи
        self.ants: list[Ant] = DataTransformer.ants_transform(data['ants'])
        if len(self.ants) == 0:
            time.sleep(1)
            return
        
        # распределяем муравьев по отдельным группам
        self.scouts: list[Ant] = []
        self.soldiers: list[Ant] = []
        self.workers: list[Ant] = []
        for ant in self.ants:
            if isinstance(ant, ScoutAnt):
                self.scouts.append(ant)
            elif isinstance(ant, SoldierAnt):
                self.soldiers.append(ant)
            elif isinstance(ant, WorkerAnt):
                self.workers.append(ant)

        # видимые враги
        self.enemies: list[Ant] = DataTransformer.enemies_transform(data['enemies'])

        # Видимые ресурсы
        self.food: list[Food] = DataTransformer.food_transform(data['food'])
        # Сопоставление id муравьев с единицей еду, которую муравей собирает
        self.handled_food : dict[Ant, Food] = {}

        # Координаты вашего муравейника
        self.houses: list[Vector2] = DataTransformer.houses_transform(data['home'])

        # получаем координаты клеток вокруг муравейника
        if self.cells_around_base is None:
            cells: list[Vector2] = []
            for cell in self.houses:
                cells += self.get_cells_around(cell.q, cell.r)
            temp = set(cells)
            for cell in self.houses:
                temp.remove(Vector2(cell.q, cell.r))
            self.cells_around_base = temp

        # Видимые гексы карты
        self.map: Map = DataTransformer.map_transform(data['map'])

        # позиции всех юнитов на карте
        self.units_poses: set[Vector2] = self.get_all_units_poses()

        # Количество секунд до следующего хода
        self.nextTurnIn: int = data['nextTurnIn'] 

        # Текущий счёт команды
        self.score: int = data['score'] 

        # Координаты основного гекса муравейника
        self.spot_house: Vector2 = Vector2.from_dict(data['spot'])

        # Маршруты поиска еды для работников и для скаутов
        self.search_spiral_worker: list[Vector2] = cube_spiral(self.spot_house, 150, 1)
        self.search_spiral_scout: list[Vector2] = cube_spiral(self.spot_house, 150, 4)

        # Узнаем координаты двух оставшихся домов
        if self.house_cell_1 is None or self.house_cell_2 is None:
            cell1, cell2 = [cell for cell in self.houses if cell != self.spot_house]
            self.house_cell_1 = Vector2(cell1.q, cell1.r)
            self.house_cell_2 = Vector2(cell2.q, cell2.r)

        # проверяем, что ход новый и начинаем новый ход
        if data['turnNo'] != self.turnNo:
            self.turnNo = data['turnNo'] # номер текущего хода
            self.new_turn()

        # отправляем запрос на движение муравьев
        self.post_move(self.moves)
    
    def get_all_units_poses(self) -> set[Vector2]:
        '''
        Получает позиции всех известных юнитов на карте
        '''
        units_poses: set[Vector2] = set()
        for ant in self.ants:
            units_poses.add(Vector2(ant.q, ant.r))
        for enemy in self.enemies:
            units_poses.add(Vector2(enemy.q, enemy.r))
        return units_poses

    def bad_tile(self, i: Vector2) -> bool:
        return self.map[i].type == HexType.ROCK.value or \
               i in self.units_poses

    def pathcost(self, path: list[Vector2]) -> int:
        i = 0
        for tile in path:
            i += self.map[tile].cost
        return i

    def filter_path(self, path: list[Vector2]) -> list[Vector2]:
        output = path.copy()
        for i in range(1, len(output) - 1):
            if self.bad_tile(output[i]):
                n = neighbors(output[i].q, output[i].r) 
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
        '''
        Отправка запроса на движение муравьев
        '''
        data = {
            "moves": moves
        }
        data = requests.post(URL + 'move', headers=HEADERS, json=data).json()
        self.nextTurnIn: int = data['nextTurnIn']
        time.sleep(self.nextTurnIn)


    def register(self) -> None:
        print(requests.post(URL+'register', headers=HEADERS).json())

    def search_state(self, ant : Ant) -> list[Vector2]:
        '''
        Состояние поиска муравья. Ищет позицию муравья в спирали и двигает его
        '''
        
        l = self.search_spiral_scout if ant.type == AntType.SCOUT \
                                     else self.search_spiral_worker
        idx = l.index(Vector2(ant.q, ant.r))
        return self.filter_path(l[idx:idx+ant.SPEED+1])

    def goto_food_state(self, ant: Ant) -> list[Vector2]:
        '''
        Состояние движения к еде. Муравей движется напрямую, пока не дойдет до еды
        '''
        end = self.handled_food[ant]
        return self.get_hex_path_odd_r(ant.q, ant.r, end.q, end.r)[:ant.SPEED+1]

    def goto_base_state(self, ant: Ant) -> list[Vector2]:
        '''
        Состояние движения на базу. Муравей движется НЕ на базовую клетку, после возвращается на ближайшую клетку спирали (мб и не ближайшую, зависит от реализации)
        '''

        if ant.food is not None and ant.food.amount > 0: 
            point = self.house_cell_1 \
                    if self.get_distance(ant.q, ant.r, 
                                         self.house_cell_1.q, 
                                         self.house_cell_1.r) < \
                       self.get_distance(ant.q, ant.r, 
                                         self.house_cell_1.q, 
                                         self.house_cell_1.r) \
                     else self.house_cell_2
            return self.get_hex_path_odd_r(ant.q, ant.r, point.q, point.r)[:ant.SPEED+1]

        else:
            l = self.search_spiral_scout if ant.type == AntType.SCOUT \
                                     else self.search_spiral_worker
            return self.get_hex_path_odd_r(ant.q, ant.r, l[10].q, l[10].r)[:ant.SPEED+1] 

    def worker_logic(self) -> None:
        # Нужно сделать правильную аннотацию
        ant_state: dict[StateType, Any] = \
            {StateType.SEARCH: lambda ant: self.search_state(ant),
             StateType.GOTO_FOOD: lambda ant: self.goto_food_state(ant),
             StateType.GOTO_BASE: lambda ant: self.goto_base_state(ant)
             }

        # Присваиваем работникам единицы еды
        for ant in self.workers:
            if ant.id not in self.handled_food:
                for food in self.food:
                    if food not in self.handled_food.values():
                        self.handled_food[ant] = food
                        break;

        # Присваиваем работникам состояния
        for ant, food in self.handled_food.items():
            if ant.food is not None and ant.food.amount > 0:
                ant.state = StateType.GOTO_BASE
            else:
                ant.state = StateType.GOTO_FOOD
            # Если муравья нет в этом списке, то state == SEARCH

        # Запускаем состояния и делаем запросы
        for ant in self.workers:
            path = ant_state[ant.state](ant)
            self.moves.append({ant.id: path})
            
        # Дальше все сделает self.post_move


def main() -> None:
    app = App()
    # print(app.get_hex_path_odd_r(3, 6, 4, 5))
    app.register()

    while True:
        app.get_arena()


if __name__ == '__main__':
    main()

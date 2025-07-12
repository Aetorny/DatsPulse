from typing import Any
import requests
import time
from models.ants.ant import Ant
from models.map import Map
from models.food import Food
from models.vector2 import Vector2
from models.ants.soldier import SoldierAnt
from models.ants.scout import ScoutAnt
from models.ants.worker import WorkerAnt
from models.hex_type import HexType
import json
from collections import deque
from controller.transformer import DataTransformer
from controller.settings import *
from collections import defaultdict


class Controller:
    def __init__(self) -> None:
        self.scouts: list[ScoutAnt] = []
        self.soldiers: list[SoldierAnt] = []
        self.soldiers_positions: set[Vector2] = set()
        self.cells_around_base: set[Vector2] | None = None
        self.workers: list[WorkerAnt] = []
        self.moves: list[dict[str, Any]] = []
        self.turnNo: int = -1

        self.is_run = True

    def get_distance(self, q1: int, r1: int, q2: int, r2: int) -> int:
        '''
        Вычисление расстояния между двумя геками
        '''
        assert isinstance(q1, int) and isinstance(r1, int) and isinstance(q2, int) and isinstance(r2, int), 'q and r must be int'
        x1 = q1 - (r1 - (r1 & 1)) // 2
        z1 = r1
        y1 = -x1 - z1

        x2 = q2 - (r2 - (r2 & 1)) // 2
        z2 = r2
        y2 = -x2 - z2

        distance = max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))

        return distance

    def get_cells_around(self, q: int, r: int) -> list[Vector2]:
        '''
        Получение клеток вблизи другой клетки
        '''
        cells = [Vector2(q, r-1), Vector2(q, r+1), Vector2(q-1, r), Vector2(q+1, r)]
        if r % 2 == 0:
            temp_col = q - 1
        else:
            temp_col = q + 1
        cells.append(Vector2(temp_col, r-1))
        cells.append(Vector2(temp_col, r+1))
        return cells

    def move_soldiers_to_guard(self) -> None:
        '''
        Передвижение солдат на смежные клетки с домами для защиты
        '''
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
        assert isinstance(soldier, SoldierAnt), 'soldier must be SoldierAnt'

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

    def get_path(self, q_start: int, r_start: int, q_end: int, r_end: int) -> list[Vector2] | None:
        '''
        Найти ближайший путь от А до Б

        Поиск в ширину
        '''
        DIRECTIONS = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0), Vector2(1, 1), Vector2(-1, -1)]

        path: list[Vector2] = []
        graph = defaultdict(set)

        start_coord: Vector2 = Vector2(q_start, r_start)
        end_coord: Vector2 = Vector2(q_end, r_end)


        queue: deque[Vector2] = deque()
        queue.append(start_coord)

        visited: set[Vector2] = set()

        while queue:
            coord = queue.pop()
            if coord == end_coord:
                break
            visited.add(coord)
            for d in DIRECTIONS:
                # генерируем новую координату, которую надо посетить
                new_coord = coord + d
                # если попался камень или клетка уже посещена - пропускаем
                if (new_coord in self.map and self.map[new_coord].type == HexType.ROCK) or new_coord in visited:
                    continue
                # добавляем в очередь
                queue.appendleft(new_coord)
                # добавляем в граф
                graph[coord].add(new_coord)
        
        path: list[Vector2] = []
            
        cur_coord = end_coord
        while cur_coord != start_coord:
            path.append(cur_coord)
            for key, value in graph.items():
                if cur_coord in value:
                    cur_coord = key
                    continue
        
        return path
        
    
    def move_ant(self, ant_id: str, path: list[Vector2]) -> None:
        '''
        Добавляет путь движения муравья к запросу
        '''
        self.moves.append({
            'ant': ant_id,
            'path': list(map(lambda v: v.to_dict(), path))
        })

    def get_the_nearest_food_to_house(self) -> Food:
        '''
        Получить ближайшую еду к дому
        '''
        return min(self.food, key=lambda f: self.get_distance(self.spot_house.q, self.spot_house.r, f.q, f.r))
    
    def go_to_food(self) -> None:
        '''
        Идти добывать еду
        '''
        for worker in self.workers:
            if worker.food is None:
                target = self.get_the_nearest_food_to_house()
                path = self.get_path(worker.q, worker.r, target.q, target.r)
            else:
                path = self.get_path(worker.q, worker.r, self.spot_house.q, self.spot_house.r)
            if path is not None:
                self.move_ant(worker.id, path)
    
    def set_cells_around_base(self) -> None:
        '''
        Просчитывает координаты смежных клеток с домом
        '''
        cells: list[Vector2] = []
        for cell in self.houses:
            cells += self.get_cells_around(cell.q, cell.r)
        temp = set(cells)
        for cell in self.houses:
            temp.remove(Vector2(cell.q, cell.r))
        self.cells_around_base = temp

    def new_turn(self) -> None:
        '''
        Просчитывание нового хода
        '''
         # получаем координаты клеток вокруг муравейника
        if self.cells_around_base is None:
            self.set_cells_around_base()
        
        assert self.cells_around_base, 'cells_around_base must not be None'

        # двигаем солдат на смежные клетки для защиты
        if len(self.soldiers) - 1 < len(self.cells_around_base):
            self.move_soldiers_to_guard()
        
        self.go_to_food()
    
    def save_response(self, data: dict, filename: str = 'test.json'):
        '''
        Сохраняет ответ запроса в файл
        '''
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)


    def post_move(self, moves: list[dict[str, Any]]) -> None:
        '''
        Отправка запроса на движение муравьев
        '''
        data = {
            'moves': moves
        }
        data = requests.post(URL + '/move', headers=HEADERS, json=data).json()
        self.nextTurnIn: int = data['nextTurnIn']
        time.sleep(self.nextTurnIn)


    def register(self) -> None:
        '''
        Регистрируется на раунд
        '''
        print(requests.post(URL + '/register', headers=HEADERS).json())

    def update_arena(self) -> None:
        '''
        Обновляет данные об арене
        '''
        # получаем данные
        response = requests.get(URL + '/arena', headers=HEADERS)
        data: dict[str, Any] = response.json()
        if data.get('error', None):
            return print(data)
        
        # сохраняем response в файл
        # self.save_response(data)

        # МУРАВЬИ
        self.ants: list[Ant] = DataTransformer.ants_transform(data['ants'])
        # распределяем муравьев по отдельным группам
        self.scouts: list[ScoutAnt] = []
        self.soldiers: list[SoldierAnt] = []
        self.workers: list[WorkerAnt] = []
        for ant in self.ants:
            if isinstance(ant, ScoutAnt):
                self.scouts.append(ant)
            elif isinstance(ant, SoldierAnt):
                self.soldiers.append(ant)
            elif isinstance(ant, WorkerAnt):
                self.workers.append(ant)

        # ВРАГИ
        self.enemies: list[Ant] = DataTransformer.enemies_transform(data['enemies'])

        # ЕДА
        self.food: list[Food] = DataTransformer.food_transform(data['food'])

        # ДОМА
        self.houses: list[Vector2] = DataTransformer.houses_transform(data['home'])

        # КАРТА
        self.map: Map = DataTransformer.map_transform(data['map'])

        # Количество секунд до следующего хода
        self.nextTurnIn: int = data['nextTurnIn'] 

        # Текущий счёт команды
        self.score: int = data['score'] 

        # Координаты основного гекса муравейника
        self.spot_house: Vector2 = Vector2.from_dict(data['spot'])

        # проверяем, что ход новый и начинаем новый ход
        if len(self.ants) == 0 or data['turnNo'] != self.turnNo:
            # обновляем номер хода
            self.turnNo = data['turnNo']
            # запускам новый ход
            self.new_turn()
            # отправляем запрос на движение муравьев
            self.post_move(self.moves)
        else:
            time.sleep(1)
            return
    
    def start(self) -> None:
        '''
        Запускает контролирование раундом
        '''
        while self.is_run:
            # обнуляем список ходов
            self.moves = []
            
            # обновляем данные об арене
            self.update_arena()

import random
from typing import Any
import requests
import time
import json
import logging

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
from collections import deque
from controller.transformer import DataTransformer
from controller.settings import *
from collections import defaultdict
from controller.geometry import cube_spiral, rand_dir, neighbors


class Controller:
    def __init__(self) -> None:
        self.scouts: list[ScoutAnt] = []
        self.soldiers: list[SoldierAnt] = []
        self.cells_around_base: set[Vector2] | None = None
        self.workers: list[WorkerAnt] = []
        self.moves: list[dict[str, Any]] = []
        self.turnNo: int = -1

        self.house_cell_1: Vector2 | None = None
        self.house_cell_2: Vector2 | None = None

        self.hc1_in: Vector2 | None = None
        self.hc1_out: Vector2 | None = None
        self.hc2_in: Vector2 | None = None
        self.hc2_out: Vector2 | None = None

        self.is_run = True
        logging.basicConfig(filename='controller.log', level=logging.INFO)
        self.moving_soldiers: dict[SoldierAnt, Vector2] = {} # солдат: random_direction

    @property
    def soldiers_positions(self):
        return set(map(lambda s: Vector2(s.q, s.r), self.soldiers))

    def _make_ins_outs(self) -> None:
        n1 = neighbors(self.house_cell_1.q, self.house_cell_1.r)
        n2 = neighbors(self.house_cell_2.q, self.house_cell_2.r)

        for i in n1:
            if self.map[i].type != HexType.ROCK and self.map[i].type != HexType.ANTHILL:
                if self.hc1_in is None:
                    self.hc1_in = i
                elif self.hc1_out is None:
                    self.hc1_out = i

        check = (self.hc1_in, self.hc1_out)
        for i in n2:
            if self.map[i].type != HexType.ROCK and self.map[i].type != HexType.ANTHILL:
                if self.hc2_in is None and i not in check:
                    self.hc2_in = i
                elif self.hc2_out is None and i not in check:
                    self.hc2_out = i


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

        # получаем клетки вокруг муравейника
        soldier = None
        for soldier in self.soldiers:
            if soldier.q == self.spot_house.q and soldier.r == self.spot_house.r:
                break
        if soldier.q != self.spot_house.q or soldier.r != self.spot_house.r:
            return

        # получаем свободные клетки для размещения
        empty_cells = list(self.cells_around_base.difference(self.soldiers_positions))
        if len(empty_cells) == 0:
            return
        assert len(empty_cells) > 0, 'empty_cells must not be empty'
        assert isinstance(soldier, SoldierAnt), 'soldier must be SoldierAnt'
        assert self.house_cell_1 and self.house_cell_2

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
                for home_cell in [self.house_cell_1, self.house_cell_2]:
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
                cell1, cell2 = self.house_cell_1, self.house_cell_2
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
                return
            for home_cell in [self.house_cell_1, self.house_cell_2]:
                if self.get_distance(soldier.q, soldier.r, home_cell.q, home_cell.r) == 1:
                    self.moves.append({
                        'ant': soldier.id,
                        'path': [{
                            'q': home_cell.q,
                            'r': home_cell.r
                        }]
                    })

    def get_path(self, q_start: int, r_start: int, q_end: int, r_end: int, is_worker: bool = False) -> list[Vector2]:
        '''
        Найти ближайший путь от А до Б

        Поиск в ширину
        '''

        path: list[Vector2] = []
        graph: dict[Vector2, set[Vector2]] = defaultdict(set)
        reverse_graph: dict[Vector2, set[Vector2]] = defaultdict(set)

        start_coord: Vector2 = Vector2(q_start, r_start)
        closest_coord = start_coord
        end_coord: Vector2 = Vector2(q_end, r_end)

        queue: deque[Vector2] = deque()
        queue.append(start_coord)

        visited: set[Vector2] = set([start_coord])

        depth = 0
        t = time.time()
        while queue:
            depth += 1
            if time.time() - t > 0.3:
                print(len(queue), f'timehehehe: {time.time() - t}')
                return []
            coord = queue.pop()
            if coord == end_coord:
                break
            elif depth > 7:
                end_coord = closest_coord
                break
            
            DIRECTIONS = [Vector2(0, 1), Vector2(0, -1), Vector2(1, 0), Vector2(-1, 0)]
            if coord.r % 2 == 1:
                DIRECTIONS.append(Vector2(1, 1))
                DIRECTIONS.append(Vector2(1, -1))
            else:
                DIRECTIONS.append(Vector2(-1, -1))
                DIRECTIONS.append(Vector2(-1, 1))
                
            for d in DIRECTIONS:
                # генерируем новую координату, которую надо посетить
                new_coord = coord + d
                # если попался камень или клетка уже посещена - пропускаем
                if is_worker:
                    ant_col = any(new_coord.q == ant.q and new_coord.r == ant.r for ant in self.workers)
                else:
                    ant_col = any(new_coord.q == ant.q and new_coord.r == ant.r for ant in self.scouts)
                en_col = any(new_coord.q == ant.q and new_coord.r == ant.r for ant in self.enemies)
                l = ant_col or en_col

                if (new_coord in self.map and (self.map[new_coord].type == HexType.ROCK or \
                    self.map[new_coord].type == HexType.ANTHILL or l)) or new_coord in visited:
                    continue
                # добавляем в очередь
                closest_coord = min(closest_coord, new_coord, key=lambda c: self.get_distance(c.q, c.r, end_coord.q, end_coord.r))
                queue.appendleft(new_coord)
                visited.add(new_coord)
                # добавляем в граф
                graph[coord].add(new_coord)
                reverse_graph[new_coord].add(coord)
        
        path: list[Vector2] = []
        cur_coord = end_coord
        while cur_coord != start_coord:
            if time.time() - t > 0.3:
                print(len(graph), f'time: {time.time() - t}')
                return []
            path.append(cur_coord)
            keys = reverse_graph[cur_coord]
            if len(keys) == 0:
                print('no path')
                return []
            cur_coord = keys.pop()
            # for key, value in graph.items():
            #     if cur_coord in value:
            #         cur_coord = key
            #         continue
        path.reverse()
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
            path = self.get_path(worker.q, worker.r, self.spot_house.q, self.spot_house.r)
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
    

    def select_soldier_to_fight(self):
        '''
        Выбирает, кого отправлять в бой из военных
        '''
        random_soldier = None
        for soldier in self.soldiers:
            if self.cells_around_base is not None and Vector2(soldier.q, soldier.r) in self.cells_around_base:
                random_soldier = soldier
                break
        assert isinstance(random_soldier, SoldierAnt)
        self.moving_soldiers[random_soldier] = random.choice([Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)])
        

    def move_soldiers(self):
        '''
        Двигает движущихся солдат
        '''
        for soldier, direction in self.moving_soldiers.items():
            pos = Vector2(soldier.q, soldier.r)
            target_pos = soldier.SPEED * direction + pos
            path = self.get_path(pos.q, pos.r, target_pos.q, target_pos.r)
            self.move_ant(soldier.id, path[:soldier.SPEED])

    def new_turn(self) -> None:
        '''
        Просчитывание нового хода
        '''
         # получаем координаты клеток вокруг муравейника
        if self.cells_around_base is None:
            self.set_cells_around_base()
        
        assert self.cells_around_base, 'cells_around_base must not be None'

        if len(self.soldiers) - len(self.moving_soldiers) > len(self.cells_around_base):
            self.select_soldier_to_fight()
        self.move_soldiers()
        self.move_soldiers_to_guard()


        # self.go_to_food()
        t = time.time()
        self.worker_logic()
        print(f'worker_logic: {time.time() - t}')
    
    def save_response(self, data: dict[str, Any], filename: str = 'response.json'):
        '''
        Сохраняет ответ запроса в файл
        '''
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def post_move(self, moves: list[dict[str, Any]]) -> None:
        '''
        Отправка запроса на движение муравьев
        '''
        logging.info(f'moves: {moves}')
        data = {
            'moves': moves
        }
        data = requests.post(URL + '/move', headers=HEADERS, json=data).json()
        logging.info(f'errors: {data.get("errors", [])}')
        self.nextTurnIn: int = data['nextTurnIn']
        print(f'nextTurnIn: {self.nextTurnIn}', time.time()-self.time)
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
        self.time = time.time()
        # сохраняем response в файл
        self.save_response(data)

        # МУРАВЬИ
        if data.get('ants', None) is None:
            return
        self.ants: list[Ant] = DataTransformer.ants_transform(data['ants'])
        if len(self.ants) == 0:
            return
        # распределяем муравьев по отдельным группам
        self.scouts: list[ScoutAnt] = []
        self.soldiers: list[SoldierAnt] = []
        self.workers: list[WorkerAnt] = []
        logging.info(f'ants: {[(ant.id, ant.q, ant.r) for ant in self.ants]}')
        for ant in self.ants:
            if ant.type == AntType.SCOUT:
                self.scouts.append(ant)
            elif ant.type == AntType.FIGHTER:
                self.soldiers.append(ant)
            elif ant.type == AntType.WORKER:
                self.workers.append(ant)

        # ВРАГИ
        self.enemies: list[Ant] = DataTransformer.enemies_transform(data['enemies'])

        # ЕДА
        self.food: list[Food] = DataTransformer.food_transform(data['food'])
        # Сопоставление id муравьев с единицей еду, которую муравей собирает
        self.handled_food : dict[Ant, Food] = {}

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


        # Маршруты поиска еды для работников и для скаутов
        self.search_spiral_worker: list[Vector2] = cube_spiral(self.spot_house, 150, 1)
        self.search_spiral_scout: list[Vector2] = cube_spiral(self.spot_house, 150, 4)

        # Узнаем координаты двух оставшихся домов
        if self.house_cell_1 is None or self.house_cell_2 is None:
            cell1, cell2 = [cell for cell in self.houses if cell != self.spot_house]
            self.house_cell_1 = Vector2(cell1.q, cell1.r)
            self.house_cell_2 = Vector2(cell2.q, cell2.r)

        # Bebra
        self._make_ins_outs()

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

    def search_state(self, ant : Ant) -> list[Vector2]:
        '''
        Состояние поиска муравья. Ищет позицию муравья в спирали и двигает его
        '''
        
        l = self.search_spiral_scout if ant.type == AntType.SCOUT \
                                     else self.search_spiral_worker
        # рандомизация выхода с базы
        # if self.get_distance(ant.q, ant.r, self.house_cell_1.q, self.house_cell_2.r) < 5:
        #     d = rand_dir()
        #     return self.get_path(ant.q, ant.r, ant.q+d.q, ant.r+d.r)

        if Vector2(ant.q, ant.r) not in l:
            endpoint: Vector2 = l[0]
            for i in l:
                if self.get_distance(ant.q, ant.r, endpoint.q, endpoint.r) > \
                   self.get_distance(ant.q, ant.r, i.q, i.r):
                    endpoint = i
        else:
            idx = l.index(Vector2(ant.q, ant.r))
            endpoint = l[idx+ant.SPEED+1]
        is_worker = ant.type == AntType.WORKER
        return self.get_path(ant.q, ant.r, endpoint.q, endpoint.r, is_worker=is_worker)[:ant.SPEED]


    def goto_food_state(self, ant: Ant) -> list[Vector2]:
        '''
        Состояние движения к еде. Муравей движется напрямую, пока не дойдет до еды
        '''
        end = self.handled_food[ant]
        return self.get_path(ant.q, ant.r, end.q, end.r, is_worker=True)[:ant.SPEED]

    def goto_base_state(self, ant: Ant) -> list[Vector2] | None:
        '''
        Состояние движения на базу. Муравей движется НЕ на базовую клетку, после возвращается на ближайшую клетку спирали (мб и не ближайшую, зависит от реализации)
        '''

        assert self.house_cell_1 and self.house_cell_2
        if self.get_distance(ant.q, ant.r, self.hc1_in.q, self.hc1_in.r) < \
            self.get_distance(ant.q, ant.r, self.hc2_in.q, self.hc2_in.r):
            point = self.hc1_in
            for ant in self.workers:
                if ant.q == self.hc1_in.q and ant.r == self.hc1_in.r:
                    point = self.hc2_in
        else:
            point = self.hc2_in

        if ant.q == point.q and ant.r == point.r:
            point = self.house_cell_1 if point == self.hc1_in else self.house_cell_2
            return [point]

        out = self.get_path(ant.q, ant.r, point.q, point.r, is_worker=True)
        return out[:ant.SPEED]

    def worker_logic(self) -> None:
        # Нужно сделать правильную аннотацию
        ant_state: dict[StateType, Any] = {
            StateType.SEARCH: lambda ant: self.search_state(ant),       # type: ignore
            StateType.GOTO_FOOD: lambda ant: self.goto_food_state(ant), # type: ignore
            StateType.GOTO_BASE: lambda ant: self.goto_base_state(ant), # type: ignore
        }

        # Присваиваем работникам единицы еды
        for ant in self.workers:
            for food in self.food:
                if food not in self.handled_food.values():
                    self.handled_food[ant] = food
                    break

        has_gotofood = False
        # Присваиваем работникам состояния
        for ant, food in self.handled_food.items():
            if ant.food.amount > 0 and not has_gotofood:
                ant.state = StateType.GOTO_BASE
                has_gotofood = True
            else:
                ant.state = StateType.GOTO_FOOD
            # Если муравья нет в этом списке, то state == SEARCH

        # Запускаем состояния и делаем запросы
        print(len(self.workers))

        for ant in self.workers:
            if ant.q == self.house_cell_1.q and ant.r == self.house_cell_1.r:
                self.move_ant(ant.id, [self.hc1_out])
            elif ant.q == self.house_cell_2.q and ant.r == self.house_cell_2.r:
                self.move_ant(ant.id, [self.hc2_out])
            else:
                if len(self.workers) >= 20 and ant.q == self.spot_house.q and ant.r == self.spot_house.r:
                    continue
                self.move_ant(ant.id, ant_state[ant.state](ant))

        for ant in self.scouts:
            self.move_ant(ant.id, [Vector2(ant.q, ant.r+1)])
            
        # Дальше все сделает self.post_move

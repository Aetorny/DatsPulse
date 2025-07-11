from models.map import Map
from models.hex import Hex
from models.hex_type import HexType
from models.food import Food
from models.food_type import FoodType
from models.ants.ant import Ant
from models.ants.ant_type import AntType
from models.ants.worker import WorkerAnt
from models.ants.soldier import SoldierAnt
from models.ants.scout import ScoutAnt
from models.vector2 import Vector2


class DataTransformer:
    @staticmethod
    def map_transform(data: list[dict[str, int]]) -> Map:
        hexagons: list[Hex] = []
        for hex in data:
            hexagons.append(Hex(
                type=HexType(hex['type']),
                q=hex['q'],
                r=hex['r'],
                cost=hex['cost']
            ))
        return {Vector2(hex.r, hex.q): hex for hex in hexagons}

    @staticmethod
    def food_transform(data: list[dict[str, int]]) -> list[Food]:
        food_list: list[Food] = []
        for food in data:
            food_list.append(Food.from_dict(food))
        return food_list
    
    @staticmethod
    def ants_transform(data: list[dict]) -> list[Ant]:
        ants: list[Ant] = []
        for ant in data:
            if ant['type'] == AntType.WORKER.value:
                ants.append(WorkerAnt.from_dict(ant))
            elif ant['type'] == AntType.FIGHTER.value:
                ants.append(SoldierAnt.from_dict(ant))
            elif ant['type'] == AntType.SCOUT.value:
                ants.append(ScoutAnt.from_dict(ant))
        return ants
    
    @staticmethod
    def enemies_transform(data: list[dict]) -> list[Ant]:
        ants: list[Ant] = []
        for ant in data:
            if ant['type'] == AntType.WORKER.value:
                ants.append(WorkerAnt.from_dict(ant | {'id': ''}))
            elif ant['type'] == AntType.FIGHTER.value:
                ants.append(SoldierAnt.from_dict(ant | {'id': ''}))
            elif ant['type'] == AntType.SCOUT.value:
                ants.append(ScoutAnt.from_dict(ant | {'id': ''}))
        return ants
    
    @staticmethod
    def houses_transform(data: list[dict]) -> list[Vector2]:
        houses: list[Vector2] = []
        for house in data:
            houses.append(Vector2(house['q'], house['r']))
        return houses

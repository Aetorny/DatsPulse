from dataclasses import dataclass
from models.food_type import FoodType


@dataclass
class Food:
    q: int # столбец
    r: int # строка
    type: FoodType
    amount: int # количество

    @staticmethod
    def from_dict(data: dict[str, int]) -> 'Food':
        return Food(
            type=FoodType(data['type']),
            q=data['q'],
            r=data['r'],
            amount=data['amount']
        )

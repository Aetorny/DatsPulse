from dataclasses import dataclass
from models.hex_type import HexType


@dataclass
class Hex:
    type: HexType # тип
    q: int # столбец
    r: int # строка
    cost: int # стоимость

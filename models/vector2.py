from typing import Any


class Vector2:
    def __init__(self, q: int, r: int):
        self.q = q
        self.r = r

    def __hash__(self) -> int:
        return hash((self.q, self.r))
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return NotImplemented
        return self.q == other.q and self.r == other.r
    
    def __iter__(self):
        yield self.q
        yield self.r

    def __repr__(self):
        return f"({self.q} {self.r})"
    
    def __add__(self, other: 'Vector2'):
        return Vector2(self.q + other.q, self.r + other.r)
    
    @staticmethod
    def from_dict(data: dict[str, Any]) -> 'Vector2':
        return Vector2(data['q'], data['r'])
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'q': self.q,
            'r': self.r
        }
    
    def __mul__(self, other):
        if isinstance(other, int):
            return Vector2(self.q * other, self.r * other)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

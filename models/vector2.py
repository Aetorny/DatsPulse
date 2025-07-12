class Vector2:
    def __init__(self, q: int, r: int):
        self.q = q
        self.r = r

    def __hash__(self) -> int:
        return hash((self.q, self.r))
    
    def __eq__(self, other: 'Vector2'):
        return self.q == other.q and self.r == other.r
    
    def __iter__(self):
        yield self.q
        yield self.r

    def __repr__(self):
        return f"({self.q} {self.r})"
    
    def __add__(self, other: 'Vector2'):
        return Vector2(self.q + other.q, self.r + other.r)
    
    @staticmethod
    def from_dict(data: dict) -> 'Vector2':
        return Vector2(data['q'], data['r'])
    
    def to_dict(self) -> dict:
        return {
            'q': self.q,
            'r': self.r
        }

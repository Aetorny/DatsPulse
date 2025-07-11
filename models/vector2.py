class Vector2:
    def __init__(self, q: int, r: int):
        self.q = q
        self.r = r

    def __hash__(self) -> tuple[int, int]:
        return (self.q, self.r)
    
    def __iter__(self):
        yield self.q
        yield self.r
    
    @staticmethod
    def from_dict(data: dict) -> 'Vector2':
        return Vector2(data['q'], data['r'])

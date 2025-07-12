from models.vector2 import Vector2
import random

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

def rand_dir() -> Vector2:
    l = [(1, 0, -1), (1, -1, 0), (0, -1, 1), (-1, 0, 1), (-1, 1, 0), (0, 1, -1)]
    t = l[ random.randint(0, len(l)-1) ]
    return cube_to_oddr(4*t[0], 4*t[1], 4*t[2])

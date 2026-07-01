"""RLE parser for Conway's Game of Life patterns."""

from typeguard import typechecked


@typechecked
def parse_rle(rle: str) -> frozenset[tuple[int, int]]:
    """Parse a standard Game-of-Life RLE string into a set of (row, col) coordinates.
    
    Coordinates are relative to a (0,0) top-left origin.
    'o' = alive, 'b' = dead, digits = run length, '$' = end of row, '!' = end of pattern.
    """
    cells = set()
    r, c = 0, 0
    count_str = ""

    for char in rle:
        if char.isdigit():
            count_str += char
        elif char == "b":
            count = int(count_str) if count_str else 1
            c += count
            count_str = ""
        elif char == "o":
            count = int(count_str) if count_str else 1
            for _ in range(count):
                cells.add((r, c))
                c += 1
            count_str = ""
        elif char == "$":
            count = int(count_str) if count_str else 1
            r += count
            c = 0
            count_str = ""
        elif char == "!":
            break
            
    return frozenset(cells)

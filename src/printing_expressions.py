from typing import FrozenSet, Set, Tuple, List, Dict

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]


def print_expression(expr):
    terms = []
    for cube in expr:
        if len(cube) == 0:
            terms.append("1")
        else:
            terms.append("".join(sorted(cube)))
    print(" + ".join(sorted(terms, key=lambda s: (len(s), s))))

def print_named_expression(name: str, expr):
    print(f"{name} = ", end="")
    print_expression(expr)



# Print each cube on its own line.
# Sorted by: cube size (short cubes first), lexicographic literal order
# Deterministic output (important for debugging)
def print_cubes_vertical(expr):
    for cube in sorted(expr, key=lambda c: (len(c), sorted(c))):
        if len(cube) == 0:
            print("   1")
        else:
            print("  ", "".join(sorted(cube)))


def pretty_cube(c: Cube) -> str:
    return "1" if len(c) == 0 else "".join(sorted(c))

def pretty_kernel(k: Expr) -> str:
    # short single-line representation for headers
    terms = []
    for cube in sorted(k, key=lambda c: (len(c), sorted(c))):
        terms.append("1" if len(cube) == 0 else "".join(sorted(cube)))
    return " + ".join(terms)

def print_kernel_matrix(KM, max_col_width: int = 18):
    # Print column headers
    col_headers = [pretty_kernel(k) for k in KM.cols]
    col_headers = [h if len(h) <= max_col_width else h[:max_col_width-3] + "..." for h in col_headers]

    print(" " * 10 + "  " + "  ".join(f"{h:>{max_col_width}}" for h in col_headers))
    for i, co in enumerate(KM.rows):
        row_label = pretty_cube(co)
        row_label = f"{row_label:>10}"
        row_bits = "  ".join(f"{KM.M[i][j]:>{max_col_width}}" for j in range(len(KM.cols)))
        print(row_label + "  " + row_bits)


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
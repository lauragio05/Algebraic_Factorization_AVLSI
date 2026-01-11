from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Tuple, Dict, Iterable, Optional

@dataclass(frozen=True)
class Rectangle:
    rows: frozenset[int]   # indices into KM.rows
    cols: frozenset[int]   # indices into KM.cols

    @property
    def nrows(self) -> int:
        return len(self.rows)

    @property
    def ncols(self) -> int:
        return len(self.cols)

    @property
    def area(self) -> int:
        return self.nrows * self.ncols


def _build_col_rows(KM) -> List[Set[int]]:
    """
    col_rows[j] = set of row indices i where M[i][j] == 1
    Uses KM.ones (sparse) for efficiency.
    """
    col_rows: List[Set[int]] = [set() for _ in range(len(KM.cols))]
    for (i, j) in KM.ones:
        col_rows[j].add(i)
    return col_rows


def _closure_cols_from_rows(col_rows: List[Set[int]], rows: Set[int]) -> Set[int]:
    """
    Given a set of rows R, return the maximal set of columns C*
    such that for every col in C*, rows ⊆ col_rows[col].
    """
    if not rows:
        return set()
    out = set()
    for j, rset in enumerate(col_rows):
        if rows.issubset(rset):
            out.add(j)
    return out


def enumerate_closed_rectangles(
    KM,
    min_rows: int = 2,
    min_cols: int = 2,
    max_rectangles: Optional[int] = None,
) -> List[Rectangle]:
    """
    Enumerate 'closed' rectangles (all-1 submatrices) using a DFS over column sets.

    - Start from seed columns and grow by adding more columns.
    - For a column set C, compute rows intersection R(C).
    - Compute closure columns C* from R(C) (maximal columns for those rows).
    - Record rectangle (R(C), C*) if big enough.

    Dedup by (rows, cols).
    Works well for coursework-size matrices; can blow up on huge instances.
    """
    col_rows = _build_col_rows(KM)
    ncols = len(KM.cols)

    out: List[Rectangle] = []
    seen: Set[Tuple[frozenset[int], frozenset[int]]] = set()

    def record(rows: Set[int], cols: Set[int]):
        rect = Rectangle(frozenset(rows), frozenset(cols))
        key = (rect.rows, rect.cols)
        if key in seen:
            return
        if rect.nrows >= min_rows and rect.ncols >= min_cols:
            seen.add(key)
            out.append(rect)

    def dfs(start_col: int, current_cols: List[int], current_rows: Set[int]):
        # Optional cap
        if max_rectangles is not None and len(out) >= max_rectangles:
            return

        # Compute closure on columns
        closed_cols = _closure_cols_from_rows(col_rows, current_rows)
        record(current_rows, closed_cols)

        # Try extending with a new column > start_col
        # Only try columns not already in closure; adding a column in the closure changes nothing.
        for j in range(start_col, ncols):
            if j in closed_cols:
                continue
            # New row intersection
            new_rows = current_rows & col_rows[j]
            if not new_rows:
                continue
            dfs(j + 1, current_cols + [j], new_rows)

    # Seed DFS from each column
    for j in range(ncols):
        seed_rows = set(col_rows[j])
        if not seed_rows:
            continue
        dfs(j + 1, [j], seed_rows)

    return out

def rectangle_profit_cubecount(KM, rect: Rectangle) -> int:
    """
    Profit based on cube counts.

    Let T be the union of kernel expressions in rect.cols.
    t = number of cubes in T
    r = number of rows in rect.rows

    Covered cubes = r * t
    After extraction: r cubes (co * new_node) + t cubes (definition)
    Profit = r*t - (r + t)
    """
    r = rect.nrows
    # Build T size without actually building full T: union of cubes across selected kernels
    T = set()
    for j in rect.cols:
        T |= set(KM.cols[j])
    t = len(T)

    return r * t - (r + t)

def _lit_cost_cube(cube) -> int:
    return len(cube)

def _lit_cost_expr(expr) -> int:
    return sum(_lit_cost_cube(c) for c in expr)

def rectangle_profit(KM, rect) -> int:
    """
    Literal-count profit for extracting a rectangle.

    Rectangle selects:
      - rect.rows: list/set of row indices into KM.rows (each is a Cube)
      - rect.cols: list/set of col indices into KM.cols (each is an Expr)

    We form:
      R = { KM.rows[i] for i in rect.rows }     (co-kernel cubes)
      T = union of all cubes across KM.cols[j]  (kernel cubes)

    Covered region corresponds to cubes r ∪ t for r in R, t in T.

    Extraction model:
      introduce new node X = sum(R)
      replace covered region by X * T
      pay definition cost for X

    Profit = literals_before - literals_after
    """

    # Resolve actual row cubes from indices
    R = [KM.rows[i] for i in rect.rows]

    # Union of kernel cubes across selected columns
    T = set()
    for j in rect.cols:
        T |= set(KM.cols[j])  # KM.cols[j] is Expr = set of cubes

    # BEFORE: literal cost of all unique cubes in the covered region
    covered = set()
    for r in R:
        for t in T:
            covered.add(frozenset(set(r) | set(t)))
    before = sum(len(c) for c in covered)

    # AFTER:
    # definition cost of X = sum(R)
    def_cost = sum(len(r) for r in R)

    # top-level usage: X * T  (treat X as 1 literal per product cube)
    use_cost = sum(1 + len(t) for t in T)

    after = def_cost + use_cost

    return before - after



def best_rectangle(KM, rectangles):
    best = None
    best_key = None
    for r in rectangles:
        prof = rectangle_profit(KM, r)
        key = (prof, r.area, r.nrows, r.ncols)
        if best is None or key > best_key:
            best = r
            best_key = key
    return best


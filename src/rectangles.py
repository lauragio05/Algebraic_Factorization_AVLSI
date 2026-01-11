from __future__ import annotations
from dataclasses import dataclass
from typing import List, Set, Tuple, Dict, Iterable, Optional

# We only need the KernelMatrix type at runtime.
# If you want type checking, you can import it with TYPE_CHECKING.
# from .matrix import KernelMatrix


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

def rectangle_profit(KM, rect: Rectangle) -> int:
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


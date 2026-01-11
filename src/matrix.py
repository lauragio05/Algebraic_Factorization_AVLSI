from __future__ import annotations
from dataclasses import dataclass
from typing import FrozenSet, Set, Tuple, List, Dict

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]

# ---- canonicalization helpers (critical for hashing/dedup) ----

def canon_cube(c: Cube) -> Tuple[str, ...]:
    """Canonical form of a cube for hashing/printing."""
    return tuple(sorted(c))

def canon_expr(e: Expr) -> Tuple[Tuple[str, ...], ...]:
    """
    Canonical form of an expression (SOP).
    Sort cubes deterministically, then sort literals inside each cube.
    """
    cube_keys = [canon_cube(c) for c in e]
    cube_keys.sort(key=lambda t: (len(t), t))
    return tuple(cube_keys)


@dataclass
class KernelMatrix:
    rows: List[Cube]                      # co-kernels
    cols: List[Expr]                      # kernels
    M: List[List[int]]                    # dense 0/1 matrix
    ones: Set[Tuple[int, int]]            # sparse set of (row_i, col_j) where M=1

    row_index: Dict[Cube, int]
    col_index: Dict[Tuple[Tuple[str, ...], ...], int]  # canonical kernel -> col idx


def build_kernel_matrix(pairs: List[Tuple[Cube, Expr]]) -> KernelMatrix:
    """
    Build Boolean matrix M where:
      rows = co-kernels (Cube)
      cols = kernels (Expr)
      M[i][j] = 1 iff (co_kernel_i, kernel_j) exists in pairs.

    Input:
      pairs: list of (co_kernel, kernel_expr) from kernel extraction
    """

    # 1) Collect unique co-kernels
    uniq_rows = sorted(
        {co for (co, _) in pairs},
        key=lambda c: (len(c), canon_cube(c))
    )

    # 2) Collect unique kernels, but dedup by canonical expression
    uniq_cols_canon = sorted(
        {canon_expr(k) for (_, k) in pairs},
        key=lambda ce: (len(ce), ce)
    )

    # 3) Build index maps
    row_index = {co: i for i, co in enumerate(uniq_rows)}
    col_index = {ck: j for j, ck in enumerate(uniq_cols_canon)}

    # 4) Recover actual Expr objects for cols (pick one representative per canonical form)
    #    (We need to display/print actual kernels later.)
    rep_kernel: Dict[Tuple[Tuple[str, ...], ...], Expr] = {}
    for _, k in pairs:
        ck = canon_expr(k)
        if ck not in rep_kernel:
            rep_kernel[ck] = set(k)

    uniq_cols = [rep_kernel[ck] for ck in uniq_cols_canon]

    # 5) Fill sparse ones
    ones: Set[Tuple[int, int]] = set()
    for co, k in pairs:
        i = row_index[co]
        j = col_index[canon_expr(k)]
        ones.add((i, j))

    # 6) (Optional) build dense matrix
    m = [[0] * len(uniq_cols) for _ in range(len(uniq_rows))]
    for (i, j) in ones:
        m[i][j] = 1

    return KernelMatrix(
        rows=uniq_rows,
        cols=uniq_cols,
        M=m,
        ones=ones,
        row_index=row_index,
        col_index=col_index,
    )

# src/factor.py
from __future__ import annotations
from typing import Dict, FrozenSet, Set, Tuple, Iterable

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]


def _union_expr(exprs: Iterable[Expr]) -> Expr:
    """OR (sum) of expressions -> set union of cubes."""
    out: Expr = set()
    for e in exprs:
        out |= set(e)
    return out


def _multiply_cube_expr(co: Cube, e: Expr) -> Expr:
    """Distribute cube 'co' into SOP expression e: co * sum(cubes) = sum(co ∪ cube)."""
    out: Expr = set()
    co_set = set(co)
    for c in e:
        out.add(frozenset(co_set | set(c)))
    return out


def apply_rectangle_once(
    F: Expr,
    KM,
    rect,
    *,
    new_node: str,
    strict: bool = False,
    warn: bool = True,
) -> Tuple[Expr, Dict[str, Expr], Expr]:
    """
    Apply one rectangle extraction to the current expression F.

    Inputs:
      F        : current SOP expression (set of cubes)
      KM       : KernelMatrix from build_kernel_matrix(pairs)
      rect     : Rectangle from rectangles.py (rows/cols are index sets)
      new_node : name of new intermediate literal (e.g., "t1")
      strict   : if True, raise error when rectangle expansion covers cubes not present in F
      warn     : if True, print a warning when coverage isn't exact (strict=False)

    What it does:
      1) Builds T = union of kernel expressions in selected columns.
      2) Computes covered = union over selected rows of (co_kernel_row * T).
      3) Removes covered cubes from F (only those actually present, unless strict=True).
      4) Adds replacement cubes: for each selected co-kernel row r, add (r ∪ {new_node}).
      5) Returns:
           newF      : rewritten expression using new_node
           defs      : { new_node : T } definition of new node
           removed   : the set of cubes that were removed from F

    Returns:
      (newF, defs, removed)
    """

    # --- 1) T = union of selected kernels (columns) ---
    if not rect.cols:
        raise ValueError("Rectangle has no columns; cannot extract.")

    selected_kernel_exprs = [KM.cols[j] for j in rect.cols]
    T: Expr = _union_expr(selected_kernel_exprs)

    # --- 2) covered = union_{i in rect.rows} (KM.rows[i] * T) ---
    if not rect.rows:
        raise ValueError("Rectangle has no rows; cannot extract.")

    covered: Expr = set()
    for i in rect.rows:
        co: Cube = KM.rows[i]
        covered |= _multiply_cube_expr(co, T)

    # --- 3) remove covered cubes from F (exactly or best-effort) ---
    missing = covered - F
    if missing:
        if strict:
            # show a small sample to help debug
            sample = list(missing)[:10]
            sample_str = ["".join(sorted(c)) if c else "1" for c in sample]
            raise RuntimeError(
                f"Rectangle expansion covers {len(missing)} cube(s) not present in F. "
                f"Sample missing cubes: {sample_str}"
            )
        if warn:
            print(
                f"[WARN] Rectangle expansion produced {len(missing)} cube(s) not present in F; "
                f"removing only those cubes that actually appear."
            )

    removed: Expr = covered & F
    newF: Expr = set(F) - removed

    # --- 4) add replacement cubes: co * new_node for each selected row ---
    for i in rect.rows:
        co: Cube = KM.rows[i]
        newF.add(frozenset(set(co) | {new_node}))

    # --- 5) store definition ---
    defs: Dict[str, Expr] = {new_node: T}
    return newF, defs, removed

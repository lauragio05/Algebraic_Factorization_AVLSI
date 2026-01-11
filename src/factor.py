# src/factor.py
from __future__ import annotations
from typing import Dict, FrozenSet, Set, Tuple, Iterable
from .kernel import common_cube

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

def extract_common_cube_once(F: Expr):
    """
    Perform one algebraic common-cube extraction on F, if possible.

    Example:
      {dt1, et1} -> {t1d, t1e} -> t1*(d+e)

    Returns:
      (newF, changed)
    """
    if len(F) < 2:
        return F, False

    # Try all subsets of size >= 2 implicitly by grouping
    cubes = list(F)

    for i in range(len(cubes)):
        base = cubes[i]

        # Group all cubes sharing something with base
        group = {c for c in F if c & base}

        if len(group) < 2:
            continue

        cc = common_cube(group)
        if not cc:
            continue

        # Build remainder expression
        remainder = {frozenset(c - cc) for c in group}

        # Remove old cubes
        newF = set(F) - group

        # Add factored form: cc * remainder
        for r in remainder:
            newF.add(frozenset(cc | r))

        return newF, True

    return F, False

def extract_single_row_node_once(F: Expr, *, node_prefix: str, next_id: int):
    """
    Extract a node from patterns like:
        {acd, ace, bcd, bce} -> {t1d, t1e} -> t1*(d+e)  with t1 = a*b*c

    Returns:
        (newF, new_defs, changed, next_id)
    """
    cubes = list(F)

    for base in cubes:
        # Find all cubes sharing a common cube with base
        group = {c for c in F if c & base}
        if len(group) < 2:
            continue

        cc = common_cube(group)
        if not cc:
            continue

        # Remainder (what will go into the new node)
        remainder = {frozenset(c - cc) for c in group}
        if len(remainder) < 2:
            continue

        # Create new node
        node = f"{node_prefix}{next_id}"
        next_id += 1

        # Definition: node = sum(remainder)
        new_defs = {node: remainder}

        # Rewrite F: remove group, add node * cc
        newF = set(F) - group
        newF.add(frozenset(set(cc) | {node}))

        return newF, new_defs, True, next_id

    return F, {}, False, next_id

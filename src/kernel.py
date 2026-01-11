from __future__ import annotations
from typing import FrozenSet, Set, List, Tuple

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]

# --- utility: cube-free test ---
def common_cube(expr: Expr) -> Cube:
    """
    Return the common cube (intersection of literals across all cubes).
    If expr is empty, return empty cube.
    Example 1: common_cube({{'a','b'},{'a','c'},{'a','d'}}) == {'a'} or frozenset({'a'})
    Example 2: common_cube({{'a','b'},{'a','b','c'},{'a','b','d'}}) == {'a','b'} or frozenset({'a','b'})
    Counter-example: common_cube({{'a','b'},{'b','c'},{'a','d'}}) == {} or frozenset()
    """
    if not expr:
        return frozenset()
    it = iter(expr)
    common = set(next(it))
    for c in it:
        common &= set(c)
    return frozenset(common)


def is_cube_free(expr: Expr) -> bool:
    """
    Cube-free iff intersection of literals across all cubes is empty.
    """
    return len(common_cube(expr)) == 0

# --- kernel extraction ---
def kernels(F: Expr) -> List[Tuple[Cube, Expr]]:
    """
    Compute kernel / co-kernel pairs of F.

    Returns list of (co_kernel, kernel_expr) pairs.
    co_kernel is a cube (frozenset of literals).
    kernel_expr is cube-free expression (set of cubes).
    """
    out: List[Tuple[Cube, Expr]] = []
    seen: Set[Tuple[Cube, Tuple[Cube, ...]]] = set()  # for dedup

    def canon_expr(expr: Expr) -> Tuple[Cube, ...]:
        # canonical ordering so we can deduplicate kernels reliably
        # This is important to avoid infinite recursion and redundant work.
        return tuple(sorted(expr, key=lambda c: (len(c), tuple(sorted(c)))))

    def recurse(expr: Expr, co: Cube):
        """
        Explore kerneling starting from expr, with current co-kernel 'co'.
        """
        if not expr:
            return

        # If cube-free, record this (co, expr) as a kernel pair.
        if is_cube_free(expr):
            key = (co, canon_expr(expr))
            if key not in seen:
                seen.add(key)
                out.append((co, set(expr)))  # copy
            # Important: even if cube-free, there may be deeper kernels too.

        # Count literal occurrences (in how many cubes each literal appears)
        lit_count = {}
        for c in expr:
            for lit in c:
                lit_count[lit] = lit_count.get(lit, 0) + 1

        # Recurse on literals that occur in >= 2 cubes
        for lit, count in sorted(lit_count.items()):
            if count < 2:
                continue

            # Build subexpression of cubes containing lit
            sub = {c for c in expr if lit in c}

            # Divide sub by lit: remove lit from each cube
            quotient = {frozenset(set(c) - {lit}) for c in sub}

            # New co-kernel = old co * lit
            new_co = frozenset(set(co) | {lit})

            recurse(quotient, new_co)

    recurse(F, frozenset())  # start with co-kernel = 1
    return out

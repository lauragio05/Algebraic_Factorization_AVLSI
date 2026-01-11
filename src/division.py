from __future__ import annotations
from typing import FrozenSet, Set, Tuple

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]


def divide_expression(F: Expr, d: Cube) -> Tuple[Expr, Expr]:
    """
    Algebraic division of expression F by cube d.

    Returns (Q, R) such that:
        F = d * Q + R

    - Q contains cubes (c - d) for every cube c in F where d ⊆ c
    - R contains cubes c in F where d ⊄ c

    Notes:
    - If d is empty (frozenset()), then Q = F and R = empty.
    - The empty cube frozenset() represents the constant 1.
      Example: dividing cube 'f' by 'f' gives empty cube -> 1.
    """
    if not isinstance(d, frozenset):
        d = frozenset(d)

    if len(d) == 0:
        return set(F), set()

    Q: Expr = set()
    R: Expr = set()

    for c in F:
        if d.issubset(c):
            Q.add(frozenset(c - d))
        else:
            R.add(c)

    return Q, R


def multiply_cube_expr(d: Cube, Q: Expr) -> Expr:
    """
    Compute d * Q (distribute cube d into every cube of Q):
        d * (sum of cubes) = sum of (d ∪ cube)
    """
    out: Expr = set()
    for qc in Q:
        out.add(frozenset(set(d) | set(qc)))
    return out


def add_expr(A: Expr, B: Expr) -> Expr:
    """
    Algebraic addition for SOP with set representation.
    (Idempotent: duplicates removed automatically.)
    """
    return set(A) | set(B)

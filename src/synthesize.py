from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Set, FrozenSet, Tuple, Optional, List

from .kernel import kernels
from .matrix import build_kernel_matrix
from .rectangles import enumerate_closed_rectangles, best_rectangle, rectangle_profit
from .factor import apply_rectangle_once
from .printing_expressions import print_cubes_vertical, pretty_cube, print_kernel_matrix

Literal = str
Cube = FrozenSet[Literal]
Expr = Set[Cube]


@dataclass
class SynthesisResult:
    """
    final_expr: rewritten expression of the output (may contain t1, t2, ...)
    defs: mapping t_i -> definition (SOP expression)
    history: optional log of chosen rectangles/scores
    """
    final_expr: Expr
    defs: Dict[str, Expr]
    history: List[dict]


def synthesize_by_rectangles(
    F: Expr,
    *,
    node_prefix: str = "t",
    start_index: int = 1,
    max_iters: int = 50,
    min_rows: int = 1,
    min_cols: int = 1,
    max_rectangles: int = 5000,
    require_positive_profit: bool = True,
    verbose: bool = False,
) -> SynthesisResult:
    """
    Iteratively:
      F -> kernels -> matrix -> rectangles -> best rectangle -> extract new node -> rewrite F
    until no profitable rectangle exists or no kernels exist.

    Returns:
      SynthesisResult(final_expr, defs, history)
    """
    current_F: Expr = set(F)
    defs: Dict[str, Expr] = {}
    history: List[dict] = []

    next_id = start_index

    for it in range(max_iters):
        # 1) kernel extraction
        pairs = kernels(current_F)
        print("Kernels extracted")
        print("thses are the pairs:")
        for idx, (co_kernel, kernel_expr) in enumerate(pairs, start=1):
            print(f"pair {idx}: co-kernel {pretty_cube(co_kernel)}")
            print("kernel:")
            print_cubes_vertical(kernel_expr)

        # Stop if nothing to build a matrix from
        if not pairs:
            if verbose:
                print("Stop: no (co-kernel, kernel) pairs (no kernels to extract).")
            break

        # 2) build matrix
        KM = build_kernel_matrix(pairs)
        print_kernel_matrix(KM)


        if verbose:
            print(f"matrix: rows={len(KM.rows)} cols={len(KM.cols)} ones={len(KM.ones)}")

        # 3) enumerate rectangles
        rects = enumerate_closed_rectangles(
            KM,
            min_rows=min_rows,
            min_cols=min_cols,
            max_rectangles=max_rectangles,
        )


        if verbose:
            print(f"rectangles: {len(rects)}")


        if not rects:
            print("No rectangles found")
            if verbose:
                print("Stop: no rectangles found.")
            break
        print("There are rectangles!")

        # 4) pick best by profit
        print("Ping")
        best = best_rectangle(KM, rects)
        print("Pong")
        if best is None:
            if verbose:
                print("Stop: no best rectangle (unexpected).")
            break

        prof = rectangle_profit(KM, best)
        print(f"Best rectangle: rows={best.nrows}, cols={best.ncols}, profit={prof}")
        print("SHOULD BE FOR BOTH")

        if verbose:
            print(f"best rectangle profit: {prof}  (rows={best.nrows}, cols={best.ncols})")

        # Stop if not beneficial
        if require_positive_profit and prof <= 0:
            if verbose:
                print("Stop: best rectangle not profitable.")
            break

        # 5) apply extraction (rewrite current_F)
        node_name = f"{node_prefix}{next_id}"
        next_id += 1

        newF, new_defs, covered = apply_rectangle_once(current_F, KM, best, new_node=node_name, strict=False, warn=True)

        # Merge defs (sanity: no overwrite)
        if node_name in defs:
            raise RuntimeError(f"Internal error: node name collision: {node_name}")
        defs.update(new_defs)

        history.append({
            "iter": it,
            "node": node_name,
            "profit": prof,
            "nrows": best.nrows,
            "ncols": best.ncols,
            "covered_cubes": len(covered),
            "node_cubes": len(new_defs[node_name]),
        })

        current_F = newF

        # Optional: early stop if expression becomes trivial
        # (Not required, but sometimes useful)
        if not current_F:
            if verbose:
                print("Stop: expression became empty (0).")
            break

    return SynthesisResult(final_expr=current_F, defs=defs, history=history)

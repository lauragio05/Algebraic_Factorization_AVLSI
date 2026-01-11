import sys
import os

# --- ensure project root is on sys.path ---
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.printing_expressions import print_expression, print_cubes_vertical, print_header
from src.parser_sop import parse_sop
from src.kernel import kernels
from src.matrix import build_kernel_matrix
from src.rectangles import (
    enumerate_closed_rectangles,
    best_rectangle,
    rectangle_profit,
)
from src.factor import apply_rectangle_once


def pretty_cube(c):
    return "1" if len(c) == 0 else "".join(sorted(c))


if __name__ == "__main__":
    # --- input expression ---
    F = parse_sop("adf + aef + bdf + bef + cdf + cef + bfg + h")

    print_header("Original F")
    print_cubes_vertical(F)

    # --- kernel extraction ---
    pairs = kernels(F)
    print_header(f"Kernel / co-kernel pairs ({len(pairs)})")
    for co, k in pairs:
        print(f"co = {pretty_cube(co)}")
        print_cubes_vertical(k)

    # --- matrix ---
    KM = build_kernel_matrix(pairs)

    # --- rectangles ---
    rects = enumerate_closed_rectangles(
        KM,
        min_rows=2,
        min_cols=1,          # allow 1-column rectangles
        max_rectangles=2000,
    )

    print_header(f"Rectangles found: {len(rects)}")
    for r in rects:
        rows = [pretty_cube(KM.rows[i]) for i in sorted(r.rows)]
        cols = [KM.cols[j] for j in sorted(r.cols)]
        prof = rectangle_profit(KM, r)
        print(f"rows={rows}, ncols={len(r.cols)}, profit={prof}")

    best = best_rectangle(KM, rects)
    if best is None:
        print("\nNo rectangle selected.")
        raise SystemExit

    print_header("Chosen rectangle")
    print("Rows:", [pretty_cube(KM.rows[i]) for i in sorted(best.rows)])
    print("Profit:", rectangle_profit(KM, best))

    # --- apply extraction ---
    newF, defs, removed = apply_rectangle_once(
        F,
        KM,
        best,
        new_node="t1",
        strict=False,
        warn=True,
    )

    print_header("Removed (covered) cubes")
    print_cubes_vertical(removed)

    print_header("Definition of t1")
    print_cubes_vertical(defs["t1"])
    print_expression(defs["t1"])
    print(defs["t1"])



    print_header("New F after extraction")
    print_cubes_vertical(newF)
    print_expression(newF)
    print(len(newF))
    print(newF)

    # --- sanity checks ---
    assert removed, "No cubes were removed; extraction did nothing."
    assert "t1" in next(iter(newF)), "New node t1 does not appear in newF."

    print("\n factor.py test PASSED")

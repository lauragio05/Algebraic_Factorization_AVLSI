import sys
import os

# --- ensure project root is on sys.path ---
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.parser_sop import parse_sop
from src.synthesize import synthesize_by_rectangles
from src.printing_expressions import print_header, print_cubes_vertical, print_expression


if __name__ == "__main__":
    # --- input expression (same as your demo) ---
    F = parse_sop("ab + ac+ef")
    assert F, "Parsed F is empty."
    assert all(isinstance(c, frozenset) for c in F), "parse_sop must return cubes as frozenset."

    # --- run full synthesis (whole thing) ---
    res = synthesize_by_rectangles(
        F,
        node_prefix="t",
        start_id=1,
        max_iters=50,
        min_rows=2,
        min_cols=1,
        max_rectangles=5000,
        require_positive_profit=True,
        verbose=False,
    )

    # --- structural checks ---
    assert res is not None, "synthesize_by_rectangles returned None."
    assert hasattr(res, "final_expr"), "Result missing final_expr."
    assert hasattr(res, "defs"), "Result missing defs."
    assert hasattr(res, "history"), "Result missing history."
    assert res.final_expr is not None, "final_expr is None."
    assert res.defs is not None, "defs is None."
    assert res.history is not None, "history is None."

    # --- behavior checks (should extract at least once for this F) ---
    assert len(res.history) or len(res.defs) >= 1, "No extraction happened (history is empty)."
    assert "t1" in res.defs, "Expected extracted node 't1' not found in defs."
    assert res.defs["t1"], "Definition for t1 is empty."

    # t1 should appear in the final expression somewhere
    assert any("t1" in cube for cube in res.final_expr), "t1 does not appear in final_expr."

    # sanity: any nodes recorded in history should exist in defs
    hist_nodes = {h["node"] for h in res.history if isinstance(h, dict) and "node" in h}
    assert hist_nodes.issubset(set(res.defs.keys())), "Some history nodes are missing from defs."

    # if we required positive profit, every step should have profit > 0
    for h in res.history:
        if isinstance(h, dict) and "profit" in h:
            assert h["profit"] > 0, f"Non-positive profit step encountered: {h}"

    # --- FINAL PRINTING (for inspection) ---
    print_header("FINAL FACTORED EXPRESSION")
    #print_cubes_vertical(res.final_expr)
    print_expression(res.final_expr)

    print_header("DEFINITIONS")
    for name, expr in res.defs.items():
        print(f"{name} =")
        #print_cubes_vertical(expr)
        print_expression(expr)

import sys
import os

# --- ensure project root is on sys.path ---
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.parser_sop import parse_sop
from src.synthesize import synthesize_by_rectangles
from src.printing_expressions import print_header, print_named_expression

def run_and_report(expr_str: str):
    F = parse_sop(expr_str)

    res = synthesize_by_rectangles(
        F,
        node_prefix="t",
        start_id=1,
        max_iters=50,
        min_rows=2,
        min_cols=1,
        max_rectangles=5000,
        require_positive_profit=True,
        factor_defs=True,
        max_def_depth=10,
        verbose=False,
    )

    did_factor = (len(res.history) > 0) or (len(res.defs) > 0)

    print_header(f"INPUT: {expr_str}")
    print_header("OUTPUT")
    print_named_expression("F", res.final_expr)


    if res.defs:
        print_header("DEFINITIONS")
        for name, expr in res.defs.items():
            print_named_expression(name, expr)



    if not did_factor:
        print("\n(No factorization found; expression returned unchanged.)\n")

    # ---- invariants you can ALWAYS assert (safe) ----
    # 1) final_expr is an Expr of frozenset literals
    assert all(isinstance(c, frozenset) for c in res.final_expr)

    # 2) defs are Expr too
    for name, expr in res.defs.items():
        assert isinstance(name, str)
        assert all(isinstance(c, frozenset) for c in expr)

    # 3) node-name collisions should never occur
    assert len(res.defs) == len(set(res.defs.keys()))

if __name__ == "__main__":
    inputs = [
        "ab+ac+ad",
        "ab+cd+ef",
        "h+bfg+dfa+dfb+dfc+efa+efb+efc+dg+ge",
    ]
    for s in inputs:
        run_and_report(s)

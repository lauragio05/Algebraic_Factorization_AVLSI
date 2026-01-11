from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Set, FrozenSet, Tuple, Optional, List

from .kernel import kernels
from .matrix import build_kernel_matrix
from .rectangles import enumerate_closed_rectangles, best_rectangle, rectangle_profit
from .factor import apply_rectangle_once, extract_common_cube_once, extract_single_row_node_once
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
    next_id: int 


def synthesize_by_rectangles(
    F: Expr,
    *,
    node_prefix: str = "t",
    start_id: int = 1,
    max_iters: int = 50,
    min_rows: int = 1,
    min_cols: int = 1,
    max_rectangles: int = 5000,
    factor_defs: bool = True,
    require_positive_profit: bool = True,
    max_def_depth: int = 10,
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

    next_id = start_id

    for it in range(max_iters):
        # 1) kernel extraction
        pairs = kernels(current_F)

        # Stop if nothing to build a matrix from
        if not pairs:
            if verbose:
                print("Stop: no (co-kernel, kernel) pairs (no kernels to extract).")
            break

        # 2) build matrix
        KM = build_kernel_matrix(pairs)
        #print_kernel_matrix(KM)


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
            newF2, new_defs, changed, next_id = extract_single_row_node_once(
                current_F,
                node_prefix=node_prefix,
                next_id=next_id,
            )
            if changed:
                # record a history event so tests and debugging see this extraction
                (node_name, node_expr), = list(new_defs.items())  # exactly one

                if verbose:
                    print(f"[iter {it}] single-row extraction:")
                    print(f"  created {node_name} = "
                        f"{' + '.join(''.join(sorted(c)) for c in node_expr)}")
                    
                history.append({
                    "iter": it,
                    "kind": "single_row",
                    "node": node_name,
                    "node_expr_size": len(node_expr),
                    "note": "single-row common-cube node extraction",
                })
                current_F = newF2
                defs.update(new_defs)
                continue
            if verbose:
                print(f"[iter {it}] stop: best rectangle not profitable and no single-row extraction")
            break


        # 4) pick best by profit
        best = best_rectangle(KM, rects)
        if best is None:
            if verbose:
                print("Stop: no best rectangle (unexpected).")
            break

        prof = rectangle_profit(KM, best)


        if verbose:
            print(f"best rectangle profit: {prof}  (rows={best.nrows}, cols={best.ncols})")

        if require_positive_profit and prof <= 0:
            newF2, new_defs, changed, next_id = extract_single_row_node_once(
                current_F,
                node_prefix=node_prefix,
                next_id=next_id,
            )
            if changed:
                (node_name, node_expr), = list(new_defs.items())

                if verbose:
                    print(f"[iter {it}] single-row extraction:")
                    print(f"  created {node_name} = "
                        f"{' + '.join(''.join(sorted(c)) for c in node_expr)}")

                history.append({
                    "iter": it,
                    "kind": "single_row",
                    "node": node_name,
                    "node_expr_size": len(node_expr),
                    "note": "single-row common-cube node extraction",
                })
                current_F = newF2
                defs.update(new_defs)
                continue

            if verbose:
                print(f"[iter {it}] stop: best rectangle not profitable and no single-row extraction")

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
    # ------------------------------------------------------------
    # Recursively factor generated node definitions (t1, t2, ...)
    # ------------------------------------------------------------
    if factor_defs and defs:
        # Worklist recursion so we factor every new definition created.
        #print("Factoring definitions...")
        work = list(defs.keys())
        seen = set()
        depth = 0

        while work and depth < max_def_depth:
            name = work.pop(0)
            if name in seen:
                continue
            seen.add(name)

            sub_F = defs[name]

            # Factor this definition (but don't recurse again inside the call;
            # we manage recursion explicitly with the worklist)
            sub_res = synthesize_by_rectangles(
                sub_F,
                node_prefix=node_prefix,
                start_id=next_id,              # keep unique node numbering globally
                max_iters=max_iters,
                min_rows=min_rows,
                min_cols=min_cols,
                max_rectangles=max_rectangles,
                factor_defs=False,             # IMPORTANT: avoid infinite recursion
                require_positive_profit=require_positive_profit,
                max_def_depth=max_def_depth,
                verbose=verbose,
            )

            # Update global next_id so future nodes don't collide
            next_id = sub_res.next_id

            # Replace the definition with its factored form
            defs[name] = sub_res.final_expr

            # Merge nested defs produced while factoring this def
            for k, v in sub_res.defs.items():
                if k in defs:
                    raise RuntimeError(f"Internal error: node name collision in defs: {k}")
                defs[k] = v
                work.append(k)

            # (optional) record in history that we factored a node definition
            if sub_res.history:
                history.append({
                    "iter": None,
                    "node": name,
                    "note": f"factored definition {name} ({len(sub_res.history)} extractions)",
                })

            depth += 1


    return SynthesisResult(final_expr=current_F, defs=defs, history=history, next_id=next_id)

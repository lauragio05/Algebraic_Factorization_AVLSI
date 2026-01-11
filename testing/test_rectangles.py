import sys, os
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.parser_sop import parse_sop
from src.kernel import kernels
from src.matrix import build_kernel_matrix
from src.rectangles import enumerate_closed_rectangles, best_rectangle, rectangle_profit
from src.printing_expressions import pretty_cube, pretty_kernel


if __name__ == "__main__":
    F = parse_sop("adf+aef+bdf+bef+cdf+cef+fh+fi+gh+gi")
    pairs = kernels(F)
    KM = build_kernel_matrix(pairs)

    rects = enumerate_closed_rectangles(KM, min_rows=2, min_cols=1, max_rectangles=2000)
    print("rectangles found:", len(rects))

    br = best_rectangle(KM, rects)
    if br is None:
        print("No useful rectangle.")
    else:
        print("Best rectangle score:", rectangle_profit(KM, br))
        print("Rows (co-kernels):")
        for i in sorted(br.rows):
            print(" ", pretty_cube(KM.rows[i]))
        print("Cols (kernels):")
        for j in sorted(br.cols):
            print(" ", pretty_kernel(KM.cols[j]))

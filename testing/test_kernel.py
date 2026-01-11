import sys
import os

THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.parser_sop import parse_sop
from src.kernel import kernels
from src.printing_expressions import print_cubes_vertical


def pretty_cube(c):
    return "1" if len(c) == 0 else "".join(sorted(c))

if __name__ == "__main__":
    F = parse_sop("adf + aef + bdf + bef + cdf + cef + bfg + h")

    pairs = kernels(F)

    print("Number of (co-kernel, kernel) pairs:", len(pairs))
    for co, k in pairs:
        print("\nco-kernel =", pretty_cube(co))
        print("kernel:")
        print_cubes_vertical(k)

import sys
import os

sys.path.append(os.path.abspath("../src"))

from src.division import divide_expression, multiply_cube_expr, add_expr
from src.parser_sop import parse_sop
from src.printing_expressions import print_expression, print_cubes_vertical

if __name__ == "__main__":
    F = parse_sop("a+ab+abc+ac")
    d = frozenset({"a"})

    Q, R = divide_expression(F, d)

    print("F:")
    print_cubes_vertical(F)

    print("\nDivisor d:", "".join(sorted(d)))

    print("\nQ (quotient):")
    print_cubes_vertical(Q)

    print("\nR (remainder):")
    print_cubes_vertical(R)

    # Verify reconstruction: d*Q + R == F
    recon = add_expr(multiply_cube_expr(d, Q), R)

    print("\nReconstructed d*Q + R:")
    print_cubes_vertical(recon)
    print("\nPretty-printed reconstructed expression:")
    print_expression(recon)

    assert recon == F, "Division check failed!"
    print("\n Division check passed.")

import sys, os
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.printing_expressions import print_expression, print_cubes_vertical
from src.parser_sop import parse_sop



if __name__ == "__main__":
    F = parse_sop("xyz + a + mn + b + pqr + c")
    print("Internal representation:")
    print(F)

    
    print("Internal representation (one cube per line):")
    print_cubes_vertical(F)

    print("\nPretty-printed expression:")
    print_expression(F)

# Test inputs:
# "adf + aef + bdf + h"
# "adf + aef + bdf + bef + cdf + cef + b
# " + h"
#"  adf   +aef+   bdf +bef   +   h  "
#"abc"
#"h"
#"ab + ab + ab"
#"ab + ba"
#"a+b++c+"
#"xyz + a + mn + b + pqr + c"
from .printing_expressions import print_expression, print_cubes_vertical

def parse_sop(expression: str):
    """
    Parse an algebraic SOP expression into a set of cubes.

    Input:
        expression: string like "adf + aef + bdf + h"

    Output:
        Set of cubes, where each cube is a frozenset of literals
    """

    # Remove spaces
    expression = expression.replace(" ", "")

    # Split into product terms (cubes)
    cube_strings = expression.split("+")

    cubes = set()

    for cube_str in cube_strings:
        if cube_str == "":
            continue

        # Each character is a literal
        cube = frozenset(cube_str)
        cubes.add(cube)

    return cubes


#Testing. This code is not run during import!
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
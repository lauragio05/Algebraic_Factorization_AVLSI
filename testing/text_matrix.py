import sys
import os

THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.parser_sop import parse_sop
from src.kernel import kernels
from src.matrix import build_kernel_matrix
from src.printing_expressions import print_kernel_matrix 

F = parse_sop("adf + aef + bdf + bef + cdf + cef + bfg + h")
pairs = kernels(F)

KM = build_kernel_matrix(pairs)
print("rows =", len(KM.rows), "cols =", len(KM.cols), "ones =", len(KM.ones))
print_kernel_matrix(KM)

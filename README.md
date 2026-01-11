# Algebraic Boolean Factorization (AVLSI Project)

## Overview

This project implements an **algebraic Boolean factorization algorithm** for Sum-of-Products (SOP) expressions, based on **kernel extraction** and **rectangle covering** techniques used in multi-level logic synthesis.

The goal is to transform a flat SOP Boolean expression into a **multi-level factored representation** that:
- reduces literal count,
- exposes common sub-expressions,
- introduces intermediate nodes (definitions),
- preserves functional equivalence.

### Example

**Input**
h + bfg + dfa + dfb + dfc + efa + efb + efc + dg + ge
**Output**
F = h + bfg + t1t2
t1 = g + f t3
t2 = d + e
t3 = a + b + c


---

## High-Level Algorithm

The synthesis flow alternates between three extraction mechanisms:

### 1. Kernel Extraction
- Computes all `(co-kernel, kernel)` pairs of an SOP expression.
- Kernels are cube-free expressions.
- Based on recursive division by literals that appear in two or more cubes.

### 2. Rectangle Extraction (Kernel Matrix Method)
- Builds a Boolean matrix:
  - rows = co-kernels
  - columns = kernels
- Searches for all-1 submatrices (rectangles).
- Extracts profitable rectangles by introducing new nodes.
- Profit is measured using **literal-count reduction**.

### 3. Single-Row Algebraic Extraction
- Handles algebraic cases not representable as rectangles, e.g.:
dt1 + et1 → t2 = d + e, F = t2t1
- Introduces a new node when a cube appears in multiple product terms.

The algorithm iterates until no further improvement is possible, then **recursively factors all generated node definitions**.

---

## Data Structures

### Core Types

```python
Literal = str
Cube    = FrozenSet[Literal]   # AND of literals
Expr    = Set[Cube]            # OR of cubes (SOP)
```

### Definitions (Nodes)
- Generated nodes are stored as:
```python
defs: Dict[str, Expr]
```
- Node literals (e.g. t1) may appear in other expressions.
- Definitions form a directed acyclic graph (DAG).

## Project Structure
Algebraic_Factorization_AVLSI/
│
├── README.md
│
├── src/
│   ├── parser_sop.py
│   ├── kernel.py
│   ├── matrix.py
│   ├── rectangles.py
│   ├── factor.py
│   ├── synthesize.py
│   ├── division.py
│   ├── printing_expressions.py
│   └── __init__.py
│
└── testing/
    ├── demo_synthesize.py
    ├── test_synthesize.py
    ├── test_kernel.py
    ├── test_rectangles.py
    ├── test_factor.py
    ├── test_division.py
    └── text_matrix.py

## File Descriptions
### [`parser_sop.py`](src/parser_sop.py)
 Parses SOP strings such as ab+ac+ad into the internal Expr representation. Handles normalization and cube deduplication.
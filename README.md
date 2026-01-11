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
```text
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
```

## File Descriptions
### [`parser_sop.py`](src/parser_sop.py)
This module is responsible for parsing Boolean expressions written in **Sum-of-Products (SOP) textual form** into the internal data structures used throughout the synthesis pipeline.

It converts strings such as:
ab + ac + ad

into the canonical internal representation:

```python
Expr = {
    frozenset({"a", "b"}),
    frozenset({"a", "c"}),
    frozenset({"a", "d"}),
}
```
#### Internal Representation
-Literal: ```str```

-Cube: ```FrozenSet[str]``` (logical AND of literals)

-Expr: ```Set[Cube]``` (logical OR of cubes)

This representation is used consistently across kernel extraction, rectangle enumeration, and factoring.

#### Main Responsibilities
Tokenize SOP expressions using '+' as the OR operator

- Convert each product term into a cube (set of literals)

- Normalize expressions by:

    - removing duplicate cubes

    - sorting literals within cubes (via ```frozenset```)

- Support the constant term:

    - an empty cube (```frozenset()```) represents logical ```1```

#### Key Functions
- ```parse_sop(expr_str: str) -> Expr```

Parses an SOP string and returns the corresponding ```Expr```.

- ```_parse_cube(term: str) -> Cube``` (internal helper)

Converts a single product term (e.g. "abc") into a cube {a,b,c}.

#### Design Notes

- The parser assumes positive literals only (no negation).

- Parsing is deliberately simple and deterministic to match coursework assumptions.

- The output expression is guaranteed to be in a normalized, hashable form suitable for:
    - kernel extraction

    - matrix construction

    - equivalence checking

This module serves as the entry point of the synthesis pipeline, ensuring all downstream algorithms operate on a clean and uniform data structure.

### [`kernel.py`](src/kernel.py)

This module implements **kernel extraction**, a fundamental operation in algebraic logic synthesis.

A *kernel* of an expression is a cube-free sub-expression obtained by dividing out a common literal (or cube) from multiple product terms. Kernel extraction exposes common algebraic structure that can later be factored.

#### Responsibilities

- Compute all `(co-kernel, kernel)` pairs of an SOP expression
- Recursively explore deeper kernels by dividing on literals
- Eliminate duplicate kernels using canonicalization
- Provide utility functions for cube analysis

#### Key Functions

- **`kernels(F: Expr) -> List[Tuple[Cube, Expr]]`**  
  Computes all kernel / co-kernel pairs of the expression `F`.  
  Each result satisfies:
  ```F = co_kernel * kernel + remainder```
  where `kernel` is cube-free.

- **`common_cube(expr: Expr) -> Cube`**  
Returns the intersection of literals common to all cubes in `expr`.  
Used both for kernel detection and algebraic factoring.

- **`is_cube_free(expr: Expr) -> bool`**  
Checks whether an expression has no common literals across all cubes.

#### Design Notes

- Kernel extraction is implemented recursively, following standard textbook algorithms.
- Canonical representations are used to avoid infinite recursion and duplicate kernels.
- This module is purely analytical: it never modifies the original expression.

---

### [`matrix.py`](src/matrix.py)

This module builds the **kernel matrix**, a Boolean matrix representation used to detect factorable patterns as rectangles.

Each matrix entry represents whether a given `(co-kernel, kernel)` pair exists.

#### Responsibilities

- Construct a Boolean matrix from kernel pairs
- Maintain mappings between matrix indices and algebraic objects
- Support both sparse and dense representations

#### Data Structure

```text
Rows    → co-kernels (Cube)
Columns → kernels (Expr)
M[i][j] = 1 if (co_kernel_i, kernel_j) exists
```

#### Key Components
- KernelMatrix (dataclass)

- Stores:
     - ```rows```: list of co-kernel cubes
     - ```cols```: list of kernel expressions
     - ```M```: dense Boolean matrix
     - ```ones```: sparse set of (row, col) positions where M = 1
     - index maps for fast lookup
- build_kernel_matrix(pairs)
Constructs a KernelMatrix from kernel extraction output.

#### Design Notes

- Canonicalization is used to deduplicate kernels.
- Sparse storage (ones) enables efficient rectangle enumeration.
- This module bridges algebraic analysis and combinatorial optimization.

### [`rectangles.py`](src/rectangles.py)
This module enumerates **rectangles (all-1 submatrices)** in the kernel matrix and evaluates their profitability for extraction.

Rectangles correspond to factorizable algebraic structures.

#### Responsibilities
- Enumerate closed rectangles in the kernel matrix
- Compute rectangle profit using literal-count reduction
- Select the best rectangle for extraction

#### Key Components
-  Rectangle (dataclass) Represents a rectangle as:
    - ```rows```: indices into kernel matrix rows
    - ```cols```: indices into kernel matrix columns
- ```enumerate_closed_rectangles``(...)`
Performs DFS-based enumeration of maximal all-1 rectangles.
-  ```rectangle_profit(...)```
Computes the literal-count profit of extracting a rectangle.

-  ```best_rectangle(...)```
Selects the rectangle with highest profit and tie-breaking criteria.

#### Design Notes
- Profit is based on literal count, not cube count, reflecting hardware cost
- Single-row rectangles are intentionally excluded here and handled separately
- Enumeration is capped to avoid combinatorial explosion

### [`division.py`](src/division.py)

This module provides algebraic division utilities for SOP expressions. It supports dividing expressions by cubes and distributing products.

#### Responsibilities
- Perform algebraic division of expressions
- Support cube-level multiplication and distribution
- Provide reusable utilities for factoring

#### Key Functions

- ```divide_expr_by_cube(expr, cube)```
Divides an expression by a cube when possible.

- ```multiply_cube_expr(cube, expr)```
Distributes a cube over an SOP expression.

#### Design Notes
- These utilities are used by both kernel extraction and factor application
- Operations preserve normalized SOP representation

### [factor.py](src/factor.py)

This module applies actual factorization steps to expressions. It modifies expressions by:
- Extracting rectangle-based nodes
- Performing single-row algebraic extraction
- Introducing new node definitions

#### Responsibilities
- Apply rectangle extraction to SOP expressions
- Introduce new intermediate nodes
- Handle algebraic cases not representable as rectangles

#### Key Functions

-  ```apply_rectangle_once(...)``` Applies a rectangle extraction:
    - Creates a new node
    - Rewrites the expression
    - Returns updated expression and definitions

- `extract_single_row_node_once(...)`
Handles patterns like:
```text
dt1 + et1 → t2 = d + e, F = t2t1
```
This captures algebraic factorizations missed by rectangle methods.

#### Design Notes
- Rectangle extraction introduces multi-cube nodes
- Single-row extraction ensures completeness of algebraic factoring
- This module performs all expression rewriting

### [synthesize.py](src/synthesize.py)

This is the top-level synthesis driver. It orchestrates kernel extraction, rectangle enumeration, factor application, and recursive definition factoring.

#### Responsibilities
- Control the iterative synthesis process
- Manage node naming and history
- Recursively factor generated definitions
- Enforce termination and profit constraints

#### Key Function

-  ```synthesize_by_rectangles(F, ...) -> SynthesisResult```
Main synthesis loop:
1. Extract kernels
2. Build kernel matrix
3. Find best rectangle
4. Apply extraction if profitable
5. Fall back to single-row extraction if needed
6. Repeat until fixed point
7. Recursively factor node definitions

#### Design Notes
- Uses a worklist-based recursion to ensure termination
- Maintains a history log of all extraction steps
- Ensures node names are unique and definitions form a DAG

### [printing_expressions.py](src/printing_expressions.py)

This module contains utilities for pretty-printing SOP expressions.

#### Responsibilities
- Convert internal Expr representation into readable text
- Ensure consistent ordering of literals and terms

#### Key Function

- `print_expression(expr)` Prints an SOP expression in human-readable form, e.g.:
```text
a + bc + def
```

#### Design Notes
- Printing logic is intentionally separated from synthesis logic
- Used by both tests and demo scripts

## Testing 

### Unit Tests
Located in testing/:
- ```test_kernel.py``` – kernel extraction
- ```test_rectangles.py ```– rectangle enumeration
- ```test_factor.py``` – extraction logic
- ```test_synthesize.py``` – end-to-end synthesis
### Demo Script
demo_synthesize.py runs synthesis on arbitrary expressions and prints the result.

## How to Run

Create and activate a virtual environment

```pyhton
python3 -m venv venv
source venv/bin/activate    # macOS / Linux
# or
venv\Scripts\activate       # Windows
```
Run synthesis demo
```pyhton
python3 testing/demo_synthesize.py
```

## Design Rationale
- Literal-count profit reflects hardware cost better than cube count.
- Single-row extraction captures algebraic factorizations not expressible as rectangles.
- Recursive factoring is managed via a worklist to ensure termination.
- The final network is a multi-level DAG representation.

## Project Status
- Kernel extraction implemented
- Rectangle enumeration and profit evaluation implemented
- Single-row algebraic extraction implemented
- Recursive multi-level factoring implemented
- Functional equivalence checking implemented
- Unit tests and demo scripts included
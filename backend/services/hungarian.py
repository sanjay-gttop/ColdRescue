"""
ColdRescue Pure-Python Exact Kuhn-Munkres (Hungarian) Algorithm.

Solves the linear sum assignment problem (minimum weight bipartite matching) exactly
for both square and rectangular cost matrices:
- Square (N == M): One-to-one perfect matching.
- Rectangular (N <= M): Matches all N workers to a subset of M jobs minimizing total cost.
- Deterministic tie-breaking using canonical index ordering.
"""
from __future__ import annotations

import math
from typing import List, Tuple


def linear_sum_assignment(cost_matrix: List[List[float]]) -> Tuple[List[int], List[int]]:
    """
    Solve minimum-weight bipartite matching using Kuhn-Munkres algorithm.

    Parameters
    ----------
    cost_matrix : 2D list of shape [num_workers, num_jobs]
                  Must have num_workers <= num_jobs.
                  If num_workers > num_jobs, caller can transpose or pad.

    Returns
    -------
    (row_ind, col_ind) : Tuple of lists of indices representing the optimal assignment.
    """
    n = len(cost_matrix)
    if n == 0:
        return [], []
    m = len(cost_matrix[0])
    if n > m:
        # Transpose so rows <= cols, then transpose result back
        transposed = [[cost_matrix[r][c] for r in range(n)] for c in range(m)]
        col_res, row_res = linear_sum_assignment(transposed)
        # Sort by row indices
        pairs = sorted(zip(row_res, col_res), key=lambda p: p[0])
        return [p[0] for p in pairs], [p[1] for p in pairs]

    # Standard Kuhn-Munkres implementation (1-indexed for ease)
    # n workers, m jobs (n <= m)
    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (m + 1)
        used = [False] * (m + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0

            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(0, m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    row_ind = []
    col_ind = []
    for j in range(1, m + 1):
        if p[j] != 0:
            row_ind.append(p[j] - 1)
            col_ind.append(j - 1)

    # Sort matching by row index for canonical order
    pairs = sorted(zip(row_ind, col_ind), key=lambda x: x[0])
    return [p[0] for p in pairs], [p[1] for p in pairs]

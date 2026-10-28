# The Projection Algorithm

Given a 3D matrix (M) and a plane (p) defined by 3 points (a,b,c) forming an isosceles triangle where dist(a,b) = dist(a,c).

## Algorithm Steps:
1. Calculate distances: Let `Dab = dist(a,b) = dist(a,c)` and `Dbc = dist(b,c)`.
2. Normalize vectors: Calculate normalized vectors `v(a,b)` and `v(a,c)`.
3. Initialize output: Define a 2D matrix `E` of size `Dab * Dbc`.
4. Initialize starting points: Let `a1 = a` and `a2 = a`.
5. Iterate over rows (`y` runs from 0 to `Dab`):
   * `a1 = a1 + v(ab)`
   * `a2 = a2 + v(ac)`
   * `p = a1`
   * `d12 = dist(a1, a2)`
   * `dp = vector(a1, a2) / d12`
   * Iterate over columns (`x1` runs from 0 to `d12`):
       * `v = M[p]` (if `p` is NOT in `M`, `v = 0`)
       * `x = (Dbc/2) - (d12/2) + x1`
       * `E[x][y] = v`
       * `p = p + dp`
6. Return the 2D matrix `E`.
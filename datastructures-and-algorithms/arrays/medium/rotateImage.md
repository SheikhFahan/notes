# Rotate Image

> **LeetCode:** [Rotate Image](https://leetcode.com/problems/rotate-image/description/)

## Problem

You are given an `n x n` 2D matrix representing an image, rotate the image by 90 degrees (clockwise).

You have to rotate the image in-place, which means you have to modify the input 2D matrix directly. DO NOT allocate another 2D matrix and do the rotation.

```
Input:  matrix = [[1,2,3],[4,5,6],[7,8,9]]
Output: [[7,4,1],[8,5,2],[9,6,3]]
```

## Solution

### Mistake made

When I tried finding the pattern I picked only one element and checked how it moves across the matrix for the rotation. Since the problem stated *rotate* and the rotation was row/column wise, I should have stepped back and looked at how whole rows/columns were shifting — the pattern is hidden in there.

Why? Because it's always better to take a holistic look at the problem first and then jump deeper, not the other way around.

### Observation

If we rotate a matrix and observe how a row is shifting, e.g.

```
    r0      r1      r2
c0  (0,0)   (0,1)   (0,2)
c1  (1,0)   (1,1)   (1,2)
c2  (2,0)   (2,1)   (2,2)
```

we observe that the shift in the spots is as follows:

```
 (0,0) -> (0,2)            (1,0) -> (0,1)
 (0,1) -> (1,2)   and      (1,1) -> (1,1)
 (0,2) -> (2,2)            (1,2) -> (2,1)
```

so we can say `(i,j) -> (j, (n-1)-i)`.

### Approach (extra space)

Iterate over all the rows and, using the formula above, build a new matrix.

### Optimal (in-place)

- Transpose the matrix and then reverse each row.
- How to transpose? The diagonal stays the same; elements on opposite sides of the diagonal are swapped.

```go
func rotate(matrix [][]int) {
    n := len(matrix)
    transposeMatrix := func() {
        for row := 0; row < n; row++ {
            for col := row + 1; col < n; col++ {
                matrix[row][col], matrix[col][row] = matrix[col][row], matrix[row][col]
            }
        }
    }

    reverseRows := func() {
        for row := 0; row < n; row++ {
            for col := 0; col < n/2; col++ {
                matrix[row][col], matrix[row][n-1-col] = matrix[row][n-1-col], matrix[row][col]
            }
        }
    }

    transposeMatrix()
    reverseRows()
}
```

### Complexity

- **Time:** `O(n²)` — visit every cell once for transpose and once for reversal.
- **Space:** `O(1)` — done in place.

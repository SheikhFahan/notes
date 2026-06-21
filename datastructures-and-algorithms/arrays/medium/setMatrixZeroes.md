# Set Matrix Zeroes

> **LeetCode:** [Set Matrix Zeroes](https://leetcode.com/problems/set-matrix-zeroes/description/)

## Problem

Given an `m x n` integer matrix `matrix`, if an element is 0, set its entire row and column to 0's.

You must do it in place.

```
Input:  matrix = [[1,1,1],[1,0,1],[1,1,1]]
Output: [[1,0,1],[0,0,0],[1,0,1]]
```

## Solution

there are two ways of doing it

**1:**
- Keep list of all cells that have zero.
- Then iterate over those cells then set those rows/cols to zero

**2:** More optimized the code is for this ones in the file.
- Check if the first rows/column is to be made zero so that later first row/col can be used as indicator for the rest of the matrix.
- then iterate of the rest of the matrix and for any cell found to be zero set its respective first row/col cell to zero
- set the rows and columns to zero based on the first row column.
- set the first row/column to zero if needed.

```go
func setZeroes(matrix [][]int) {
    m, n := len(matrix), len(matrix[0])

    firstRowZero := false
    firstColZero := false

    // Check first row
    for j := 0; j < n; j++ {
        if matrix[0][j] == 0 {
            firstRowZero = true
            break
        }
    }

    // Check first column
    for i := 0; i < m; i++ {
        if matrix[i][0] == 0 {
            firstColZero = true
            break
        }
    }

    // Mark rows and columns
    for i := 1; i < m; i++ {
        for j := 1; j < n; j++ {
            if matrix[i][j] == 0 {
                matrix[i][0] = 0
                matrix[0][j] = 0
            }
        }
    }

    // Zero rows
    for i := 1; i < m; i++ {
        if matrix[i][0] == 0 {
            for j := 1; j < n; j++ {
                matrix[i][j] = 0
            }
        }
    }

    // Zero columns
    for j := 1; j < n; j++ {
        if matrix[0][j] == 0 {
            for i := 1; i < m; i++ {
                matrix[i][j] = 0
            }
        }
    }

    // Zero first row if needed
    if firstRowZero {
        for j := 0; j < n; j++ {
            matrix[0][j] = 0
        }
    }

    // Zero first column if needed
    if firstColZero {
        for i := 0; i < m; i++ {
            matrix[i][0] = 0
        }
    }
}
```

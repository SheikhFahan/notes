# Pascal's Triangle

> **LeetCode:** [Pascal's Triangle](https://leetcode.com/problems/pascals-triangle/description/)

## Problem

Given an integer `numRows`, return the first `numRows` of Pascal's triangle.

In Pascal's triangle, each number is the sum of the two numbers directly above it as shown:

```
Input:  numRows = 5
Output: [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]
```

```
      1
    1   1
  1   2   1
```

## Solution

### Observation

- in Pascals triangle all the arrays start and end with 1 regardless of the row number
- After the third array the value of any number between the ones is prevArray[index-1] + prevArray[index]

```go
func generate(numRows int) [][]int {
    pascalsTriangle := make([][]int, numRows)

    for i := 0; i < numRows; i++ {
        pascalsTriangle[i] = make([]int, i+1)
        pascalsTriangle[i][0] = 1
        pascalsTriangle[i][i] = 1

        // this loop only runs for rows with index >= 2 (the third slice onward)
        // and then populates the middle of the slice which are obtained by addition
        for j := 1; j < i; j++ {
            pascalsTriangle[i][j] = pascalsTriangle[i-1][j-1] + pascalsTriangle[i-1][j]
        }
    }
    return pascalsTriangle
}
```

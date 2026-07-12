# Merge Intervals

> **LeetCode:** [Merge Intervals](https://leetcode.com/problems/merge-intervals/description/)

## Problem

Given an array of intervals where `intervals[i] = [starti, endi]`, merge all overlapping intervals, and return an array of the non-overlapping intervals that cover all the intervals in the input.

```
Input:  intervals = [[1,3],[2,6],[8,10],[15,18]]
Output: [[1,6],[8,10],[15,18]]
```

Explanation: Since intervals [1,3] and [2,6] overlap, merge them into [1,6].

## Solution

```go
func merge(intervals [][]int) [][]int {

    if len(intervals) == 0 {
        return intervals
    }

    // sort the slice
    sort.Slice(intervals ,func(i, j int) bool {
        return intervals[i][0] < intervals[j][0]
    })

    mergedIntervals := make([][]int, 0, len(intervals))
    start, end := intervals[0][0], intervals[0][1]
    i := 1
    for i = 1; i < len(intervals); i++ {
        if intervals[i][0] <= end {
            if intervals[i][1] > end {
                end = intervals[i][1]
            }
        } else { // only append when the ranges are disjoint
            mergedIntervals = append(mergedIntervals, []int{start, end})
            start, end = intervals[i][0], intervals[i][1]
        }
    }
    
    mergedIntervals = append(mergedIntervals, []int{start, end})

    return mergedIntervals
}
```

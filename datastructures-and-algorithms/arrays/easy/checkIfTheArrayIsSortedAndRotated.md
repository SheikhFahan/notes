# Check if the Array Is Sorted and Rotated

> **LeetCode:** [Check if Array Is Sorted and Rotated](https://leetcode.com/problems/check-if-array-is-sorted-and-rotated/description/)

## Problem

Given an array `nums`, return true if the array was originally sorted in non-decreasing order, then rotated some number of positions (including zero). Otherwise, return false.

## Solution

Let's take this array for an example `[3,4,5,1,2]`

### Observation

- Given the array was originally sorted
- So If the array has a rotation then the sort would break there let's call that a drop
- If there are multiple drops that means the array is rotated more than once and return false
- The `(i+1)%lenNums` wraps around so the last→first element is also checked as a drop

```go
func check(nums []int) bool {
    lenNums := len(nums)

    drops := 0
    for i := 0; i < lenNums ; i++ {
        if nums[i] > nums[(i+1)%lenNums] {
            if (drops > 0) {
                return false
            }
            drops++
        }
    }
    return true
}
```

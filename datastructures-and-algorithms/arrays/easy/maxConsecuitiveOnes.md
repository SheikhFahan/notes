# Max Consecutive Ones

> **LeetCode:** [Max Consecutive Ones](https://leetcode.com/problems/max-consecutive-ones/)

## Problem

Given a binary array `nums`, return the maximum number of consecutive `1`'s in the array.

## Solution

Track a running count of consecutive `1`s, resetting it on every `0`, and keep the maximum seen so far.

```go
func findMaxConsecutiveOnes(nums []int) int {
    maxOnes := 0
    tempOnes := 0

    for i := 0; i < len(nums); i++ {
        if nums[i] == 1 {
            tempOnes++
        } else {
            tempOnes = 0
        }
        if tempOnes > maxOnes {
            maxOnes = tempOnes
        }
    }

    return maxOnes
}
```

### Complexity

- **Time:** `O(n)` — single pass over the array.
- **Space:** `O(1)` — only two counters.

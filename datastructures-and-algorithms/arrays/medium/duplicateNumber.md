# Find the Duplicate Number

> **LeetCode:** [Find the Duplicate Number](https://leetcode.com/problems/find-the-duplicate-number/)

## Problem

Given an array of integers `nums` containing `n + 1` integers where each integer is in the range `[1, n]` inclusive.

There is only one repeated number in `nums`, return this repeated number.

You must solve the problem without modifying the array `nums` and using only constant extra space.

```
Input:  nums = [1,3,4,2,2]
Output: 2
```

## Solution

- If there is a duplicate number and we use the elements as the Indicies to traverse then we'd inevitably be caught up in a loop.
- Moreover the opening and closing of the loop is gonna be the duplicate number.
- And the slow and the fast pointer method helps us find that point

```go
//this solution works cause the element can't be in the order of their indicies e.g [0,1,2,3] in this case their will be loops at each elemnt
// and if you remove the 0 there should not be any loop; unless one element exists twice.
func findDuplicate(nums []int) int {
    slow, fast := nums[0], nums[0]

// Treat nums as a linked list where:
// i -> nums[i]
//
// Since there are n+1 indices but only n possible values (1..n),
// the graph must contain a cycle.
//
// The duplicate value is exactly the entry point of that cycle.
    for {
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast {
            break
        }
    }

    fast = nums[0]
    for slow != fast {
        slow = nums[slow]
        fast = nums[fast]
    }

    return slow
}
```

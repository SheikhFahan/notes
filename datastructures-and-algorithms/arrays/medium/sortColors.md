# Sort Colors

> **LeetCode:** [Sort Colors](https://leetcode.com/problems/sort-colors/description/)

## Problem

Given an array `nums` with `n` objects colored red, white, or blue, sort them in-place so that objects of the same color are adjacent, with the colors in the order red, white, and blue.

We use the integers `0`, `1`, and `2` to represent red, white, and blue respectively.

```
Input:  nums = [2,0,2,1,1,0]
Output: [0,0,1,1,2,2]
```

## Solution

**1: Brute force** — sort with loops.

**2: Three pointers** (Dutch National Flag).

- `low`, `mid`, `high`
- `mid` keeps the ones in the center
- `mid` swaps the twos with `high`
- `mid` swaps the zeroes with `low`
- continue until the whole array is traversed, i.e. `mid <= high`

### Pointer

In my initial code I'd added `mid++` for all three cases. When swapping with `high`, **don't** do `mid++` — it causes a rare break: when `high` has a `0` and it's swapped into `mid`, doing `mid++` would skip over that `0` and leave a wrong value at `mid`.

```go
func sortColors(nums []int) {
    low, mid, high := 0, 0, len(nums)-1

    for mid <= high {
        switch nums[mid] {
        case 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low++
            mid++
        case 2:
            nums[high], nums[mid] = nums[mid], nums[high]
            high--
        case 1:
            mid++
        }
    }
}
```

### Complexity

- **Time:** `O(n)` — single pass.
- **Space:** `O(1)` — in place.

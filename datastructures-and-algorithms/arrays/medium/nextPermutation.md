# Next Permutation

> **LeetCode:** [Next Permutation](https://leetcode.com/problems/next-permutation/description/)

## Problem

Find the next lexicographically greater permutation.

A permutation of an array of integers is an arrangement of its members into a sequence or linear order.

For example, for `arr = [1,2,3]`, the following are all the permutations of arr: `[1,2,3]`, `[1,3,2]`, `[2,1,3]`, `[2,3,1]`, `[3,1,2]`, `[3,2,1]`.

The next permutation of an array of integers is the next lexicographically greater permutation of its integer. More formally, if all the permutations of the array are sorted in one container according to their lexicographical order, then the next permutation of that array is the permutation that follows it in the sorted container. If such arrangement is not possible, the array must be rearranged as the lowest possible order (i.e., sorted in ascending order).

## Solution

### Observation

- The next lexicographically greater permutation is the number greater than the current number and if that ain't possible then reverse of the number.
- For next permutation we have to increase number by the minimum so we come from the behind and check the first instance where `num[i] < nums[i+1]` point where we can make change in the number so that the whole number increases by a minimum `[1, (3), 5, 4, 2]`
- Then we look for the smallest number on the right of this number tat is greater than this number, given that on the right side of this number is sorted is descending order by default we come from read to the found number (breakPoint is index `(3)`). we swap these numbers `[1, (4), 5, (3), 2]`
- additionally we sort the right side of breakPoint in ascending order so that the number is the lest highet number in permutation

```go
import "slices"

// find breakpoint, swap the breakpoint values with the smalles values on the right of the breakpoint and then sort the right side of the breakpoint
func nextPermutation(nums []int)  {
    lenNums := len(nums)

    breakPoint := -1
    for i := lenNums - 2; i >= 0 ; i-- {
        if (nums[i] < nums[i+1]) { // check where the right integer > left integer
            breakPoint = i
            break
        }
    }

    if breakPoint == -1  { // if array already decending sorted then just reverse
        slices.Sort(nums)
        return
    }

    for i := lenNums-1; i >= breakPoint; i-- { // the array to the right of the breakPoint will always be sorted! our prev condition makes sure of that
        if nums[breakPoint] < nums[i] { // check if there is any other number smaller on the right side e.g for 1253 we wanna do 1325 not 1523
            nums[i], nums[breakPoint] = nums[breakPoint], nums[i]
            break
        }
    }

    slices.Sort(nums[breakPoint+1:])
}
```
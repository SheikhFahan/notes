# Merge Sorted Array

> **LeetCode:** [Merge Sorted Array](https://leetcode.com/problems/merge-sorted-array/)

## Problem

You are given two integer arrays `nums1` and `nums2`, sorted in non-decreasing order, and two integers `m` and `n`, representing the number of elements in `nums1` and `nums2` respectively.

Merge `nums1` and `nums2` into a single array sorted in non-decreasing order.

The final sorted array should not be returned by the function, but instead be stored inside the array `nums1`. To accommodate this, `nums1` has a length of `m + n`, where the first `m` elements denote the elements that should be merged, and the last `n` elements are set to `0` and should be ignored. `nums2` has a length of `n`.

```
Input:  nums1 = [1,2,3,0,0,0], m = 3, nums2 = [2,5,6], n = 3
Output: [1,2,2,3,5,6]
```

Explanation: The arrays we are merging are [1,2,3] and [2,5,6]. The result of the merge is [1,2,2,3,5,6] with the underlined elements coming from nums1.

## Solution

- Since array one is already the length of the final merged array we can use that one as the answer
- If we start from the beginning then it becomes a lot of work to rearrange the rearranged elements.
- If we start from the rear then we need not care about the swapped zeroes.
- So start from the rear of the largest array.
- After starting from the rear if there is no element left in the second array then we good cause the first one is already there.
- Otherwise if the loop stopped cause the first array got over then we run the loop for the second array and pull all the remaining elements in the beginning of the first array.

```go
func merge(nums1 []int, m int, nums2 []int, n int)  {

    i, j , itr := m - 1, n - 1, len(nums1) - 1

    for i >= 0 && j >= 0 {
        if nums1[i] > nums2[j] {
            nums1[itr] = nums1[i]
            i--
        } else if j >= 0 {
            nums1[itr] = nums2[j]
            j--
        }
        itr--
    }

    if i <= 0 {
        for j >= 0 {
            nums1[itr] = nums2[j]
            itr--
            j--
        }
    }
}
```

# Majority Element I & II

## Majority Element I

> **LeetCode:** [Majority Element](https://leetcode.com/problems/majority-element/description/)

### Problem

Given an array `nums` of size `n`, return the majority element.

The majority element is the element that appears more than `⌊n / 2⌋` times. You may assume that the majority element always exists in the array.

```
Input:  nums = [3,2,3]
Output: 3

Input:  nums = [2,2,1,1,1,2,2]
Output: 2
```

### Solution

If an element is a majority element and appears more than (n / 2) times then

- If the number of times the element is appearing is x
- then x - (n/2) > 0 i.e if the occurance of all other elements is is subtracted from "x" still "x" will be greater than Zero.

```go
func majorityElement(nums []int) int {
    cnt, elm := 0, 0 

    for _, num := range nums {
        if cnt == 0 {
            elm = num
            cnt = 1
        } else if  elm == num {
            cnt++
        } else {
            cnt--
        }
    }
    return elm
}
```

## Majority Element II

> **LeetCode:** [Majority Element II](https://leetcode.com/problems/majority-element-ii/description/)

### Problem

Given an integer array of size `n`, find all elements that appear more than `⌊n / 3⌋` times.

```
Input:  nums = [3,2,3]
Output: [3]

Input:  nums = [1]
Output: [1]

Input:  nums = [1,2]
Output: [1,2]
```

### Solution

**Observation**

- All the elements that appear more than n / 3 times can be at max 2
- If we know that this then that implies
  - let the occurance of the first and the second element be x and y respectively
    - then occurance of x + y > occurance of the rest of the elements if they exist
    - this one is an algo and TBH not very easy to come up with during an interview unless you already know the algo; don't freak out if you couldn't come up with this on yourself
    - I believed on this approach via observation and IG there would a proof for this one somewhere.

**Insight of the algo:**

- If the majority element exists then since the algo takes into account two of those from deduction of count you can see that the number that exists more than n / 3 times survives the deductions cause getting saved by cn1/2 == 0 condition. In case only one majority element exists the other condition (cnt1/2 == 0) will hit more frequently and save the majority element.

```go
func majorityElement(nums []int) []int {
    var elm1, elm2 int
    cnt1, cnt2 := 0, 0

    out := make([]int, 0, 2)

    for index := range(len(nums)) {
        if elm1 == nums[index] {
            cnt1++
        } else if elm2 == nums[index] {
            cnt2++
        } else if cnt1 == 0 {
            elm1 = nums[index]
            cnt1++
        } else if cnt2 == 0 {
            elm2 = nums[index]
            cnt2++
        } else {
            cnt1--
            cnt2--
        }
    }

    cnt1, cnt2 = 0, 0

    for _, num := range nums {
        if num == elm1 {
            cnt1++
        } else if num == elm2 {
            cnt2++
        } 
    }

    if cnt1 > len(nums)/3 {
        out = append(out, elm1)
    }

    if cnt2 > len(nums)/3{
        out = append(out, elm2)
    }

    return out
}
```

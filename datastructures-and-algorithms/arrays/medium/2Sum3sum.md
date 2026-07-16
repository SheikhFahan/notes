# Two Sum & Three Sum

## Two Sum

> **LeetCode:** [Two Sum](https://leetcode.com/problems/two-sum/)

### Problem

Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

```
Input:  nums = [2,7,11,15], target = 9
Output: [0,1]
```

Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

### Solution

**Observation**

**Brute force:**

- There is obviously 2 pointer method to solve this however that will take too long.

**Better:**

- Iterate over the array let the number in the present be "x" so "x - y == taget" is what we want; look for the "y" in the hashMap which we are populating whilst iterating over the array.

**Optimal:**

- There will always be only one solution
- The array is not sorted.
- If I sort the array and add a pointer in the rear of the array and another one to the front of the array???
- Since i need to return the indecies then i would need to store the indicies for elems somewhere; maybe in the same array but distorted if that is allowed or in another one

```go
func twoSum(nums []int, target int) []int {
    elems := make(map[int]int, len(nums))

    for currentIndex, value := range(nums) {
        compliment := target - value
        if index, ok := elems[compliment]; ok {
            return []int{currentIndex, index}
        } else {
            elems[value] = currentIndex
        }
    }

    return []int{-1, -1}
}
```

## Three Sum

> **LeetCode:** [3Sum](https://leetcode.com/problems/3sum/)

### Problem

Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

Notice that the solution set must not contain duplicate triplets.

```
Input:  nums = [-1,0,1,2,-1,-4]
Output: [[-1,-1,2],[-1,0,1]]
```

Explanation:
nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0.
nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0.
nums[0] + nums[3] + nums[4] = (-1) + 2 + (-1) = 0.
The distinct triplets are [-1,0,1] and [-1,-1,2].

### Solution

**Brute force:**

- Run the three loops and save the final answer in a set and there is your answer.

**Better solution:**

- Run two loops and then do (compliment = -(nums[i] + nums[j])) and have the compliment in a hashmap
  - If the compliment is in the hashmap then there is a triplet other wise we do not
    - What data to store in the hashMap? the data between I and J.
  - Store the found triplets in a set and then resturn unique triplets.

**Optimal Solution:**

- Since we are using set to have the unique values we can just sort the list and then we will only have unique elements i.e they will be unique by default.
- Once the list is sorted; have three pointers beginnig; rightAfterBeginning; end
  - If 3sum == 0 then we have the answer.
  - If 3sum > 0 then we need to decrease the value of 3Sum so we decrease the end.
  - If 3sum < 0 then we need to increase the value of 3Sum so we increase rightAfterBeginning.

**Also:**

- The list would have duplicate elements so we need not to process duplicate elements so we just move ahead to avoid having duplicate values in the final answer.

```go
func threeSum(nums []int) [][]int {
    sort.Ints(nums)
    triplets := [][]int{}

    for i := 0; i < len(nums) - 2; i++ {
      // If the next i is same as the old one then simple move fwd.
        if i > 0 && nums[i] == nums[i-1] {
            continue
        }

        // gotta reinit j and k after every "i" change
        j, k := i+1, len(nums) - 1
        for j < k {
            threeSum := nums[i] + nums[j] + nums[k]
            if threeSum == 0 {
                triplets  = append(triplets, []int{nums[i], nums[j], nums[k]})
                // if we don't increment/decrement and just run the loops "nums[j] == nums[j-1]" needs not to satisfy
                // and then loop goes voilent.
                j++
                k--

                // why are not we checking for the next element and the prev element
                // it is just easy this way the other code would be complicated to write.
                // We can but we are not playing ego war here. It should work; It should be simple.
                for j < k && nums[j] == nums[j-1] {
                    j++
                }
                for j < k && nums[k] == nums[k+1] {
                    k--
                }

            } else if threeSum < 0 {
                j++
            } else {
                k--
            }
        }
    }
    return triplets
}
```

# Merge Two Sorted Lists

> **LeetCode:** [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/description/)

this one is an easy on the leetcode however a hard on the striver and medium accoring to me due to doing it in contant space

## Problem

You are given the heads of two sorted linked lists `list1` and `list2`.
Merge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists.
Return the head of the merged linked list.

```
Input:  list1 = [1,2,4], list2 = [1,3,4]
Output: [1,1,2,3,4,4]
```

## Solution

**Brute force (easy):**

- Iterate over the linkedLists and keep on creating a new list as per the conditions.

**Optimal:**

- Initialize a node and think of it as a needle piercing nodes(beeds) based on the given condition (non decreasing order).
- Return the first smallest node

```go
func mergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {
    dummy := &ListNode{}
    prev := dummy   // dummy and prev point to the same memory location.
    for list1 != nil && list2 != nil {
        if list1.Val < list2.Val {
            prev.Next = list1    // sets next for dummy as well.
            list1 = list1.Next
        } else {
            prev.Next = list2
            list2 = list2.Next
        }
        
        prev = prev.Next
    }

    if list1 != nil {
        prev.Next = list1
    } else if list2 != nil {
        prev.Next = list2
    }

    return dummy.Next
}
```

# Add Two Numbers

> **LeetCode:** [Add Two Numbers](https://leetcode.com/problems/add-two-numbers/)

## Problem

You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.
You may assume the two numbers do not contain any leading zero, except the number 0 itself.

```
Input:  l1 = [2,4,3], l2 = [5,6,4]
Output: [7,0,8]
```

Explanation: 342 + 465 = 807.

## Solution

- Brute force: Create a new list and then keep on adding each nodes of the linkedlist and move forward.

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */
func addTwoNumbers(l1 *ListNode, l2 *ListNode) *ListNode {
    res := l1

    carry := 0
    prev := &ListNode{}
    for l1 != nil && l2 != nil {
        sum := l1.Val + l2.Val + carry
        if sum >= 10 {
            carry = sum / 10
            sum = sum % 10
        } else {
            carry = 0
        }

        l1.Val = sum

        prev = l1
        l1 = l1.Next
        l2 = l2.Next
    }

    if l1 == nil {
        prev.Next = l2
        l1 = l2
    }
    for l1 != nil {
        sum := l1.Val + carry
        if sum >= 10 {
            carry = sum / 10
            sum = sum % 10
        } else {
            carry = 0
        }
        l1.Val = sum
        prev = l1
        l1 = l1.Next
    }

    if carry != 0 {
        prev.Next = &ListNode{
            Val: carry,
        }
    }

    return res
}
```

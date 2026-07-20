# Reverse Linked List

> **LeetCode:** [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/)

## Problem

Given the head of a singly linked list, reverse the list, and return the reversed list.

## Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */

func reverseList(head *ListNode) *ListNode {
    var prev *ListNode // prev is null here
    for head != nil {
        next := head.Next // save the next one will need this when we have lost our head to prev
        head.Next = prev // reversing the Next pointer
        prev = head // increment previous pointer
        head = next // increment head
    }

    return prev
}
```

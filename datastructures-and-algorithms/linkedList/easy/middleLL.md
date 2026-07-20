# Middle of the Linked List

> **LeetCode:** [Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/)

## Problem

Given the head of a singly linked list, return the middle node of the linked list.
If there are two middle nodes, return the second middle node.

## Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */
func middleNode(head *ListNode) *ListNode {
    //use slow and fast pointer to find the middle of the linkedList

    slow, fast := head, head

    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    
    return slow
}
```

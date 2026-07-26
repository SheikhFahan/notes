# Intersection of Two Linked Lists

> **LeetCode:** [Intersection of Two Linked Lists](https://leetcode.com/problems/intersection-of-two-linked-lists/)

## Problem

Given the heads of two singly linked-lists headA and headB, return the node at which the two lists intersect. If the two linked lists have no intersection at all, return null.

## Solution

**Brute:**
- Traverse and use hashing

**Better:**
- Find the length of each linked list and the move the head of the larger node fwd and then move both heads together
- lenA = 10, lenB = 15; reset both to heads. move B by 5 steps first and move both together.

**Optimal:**
- a = lenX; b = lenY; traverse a and then traverse b = traverse B and then traverse A. This achieves the same thing as above but without finding the lengths.
- lenA = 10, lenB = 15; reached endA and started at B; reached endB started at A; note A will reach headB faster then B will reach headA so A gets a head start and then basically achieves the Better solution without finding the length.

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */
func getIntersectionNode(headA, headB *ListNode) *ListNode {
    a, b := headA, headB

    for a != b {
        if a != nil {
            a = a.Next
        } else {
            a = headB
        }

        if b != nil {
            b = b.Next
        } else {
            b = headA
        }
    }

    return a
}
```

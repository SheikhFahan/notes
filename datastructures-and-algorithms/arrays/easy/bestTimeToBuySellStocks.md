# Best Time to Buy and Sell Stock

> **LeetCode:** [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/)

## Problem

You are given an array `prices` where `prices[i]` is the price of a given stock on the `i`th day. You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.

Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return `0`.

```
Input:  prices = [7,1,5,3,6,4]
Output: 5
```

## Solution

**1: Brute force** — run two pointers, subtract every pair, and find the max.

**2: Best time to buy is when it is cheapest.**

### Intuition

Initially buy the stock on the first day. As you scan forward, whenever `sell < buy`, dump the old buy and buy today — you always want the least number to be subtracted from a future sell. Otherwise `sell - buy` is a candidate profit.

```go
func maxProfit(prices []int) int {
    buy := prices[0]
    maxProfit := 0

    for _, sell := range prices {
        if sell < buy {
            buy = sell
        } else if profit := sell - buy; profit > maxProfit {
            maxProfit = profit
        }
    }

    return maxProfit
}
```

### Complexity

- **Time:** `O(n)` — single pass over the prices.
- **Space:** `O(1)` — two counters.

def max_score(n, k, s):
    # 初始化 dp 数组
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    
    # 初始化连续 1 的长度
    lengths = [0] * (n + 1)
    
    for i in range(1, n + 1):
        # 如果当前字符是 1，增加连续 1 的长度
        if s[i - 1] == '1':
            lengths[i] = lengths[i - 1] + 1
        else:
            lengths[i] = 0
            
        # 更新 dp 数组
        for j in range(1, min(k + 1, i + 1)):
            # 不改变当前字符的情况
            dp[i][j] = dp[i - 1][j]
            # 改变当前字符的情况
            if s[i - 1] == '0':
                dp[i][j] = max(dp[i][j], dp[i - 1][j - 1] + lengths[i]**2)
            else:
                dp[i][j] = max(dp[i][j], dp[i - 1][j] + lengths[i]**2)
    
    return max(dp[n])

# 示例
n, k = map(int, "6 1".split())
s = "100101"
print(max_score(n, k, s))  # 输出应为 10
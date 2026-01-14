# 为什么某些 Round 可能没有 Communication Posts 的分析

## 问题概述

在 RQ3 实验中（seller communication），某些 round 可能没有 communication posts。以下是可能的原因分析：

## 主要原因

### 1. **Agent 的自主决策（最主要原因）**

**代码位置**：`oasis_market/phases.py` - `CommunicationPhase.execute()`

- Communication phase 在每个 round **开始时**执行（在 seller listing 之前）
- Agents 是 LLM 驱动的，它们会根据环境观察和 prompt 自主决定是否创建 post
- 即使 communication phase 执行了，agents 可能选择：
  - 不创建 post（如果认为没有需要分享的信息）
  - 只执行其他操作（like_post, quote_post 等）
  - 选择 `do_nothing`

**关键代码**：
```python
# CommunicationPhase 为每个 agent 提供 communication tools
communication_tools = ['create_post', 'quote_post', 'like_post', 'dislike_post']
communication_actions[agent] = LLMAction(
    extra_action=communication_tools,
    extra_prompt=communication_prompt,
    level="communication"
)
```

**结论**：这是正常行为 - agents 不是强制要求创建 post，而是根据策略自主决定。

### 2. **structured_info 字段过滤问题**

**代码位置**：
- `oasis/social_platform/platform.py` - `create_post()` 方法
- `visualization/scripts/rq3_visualization.py` - `_load_communication_data()` 方法

**问题**：
- 创建 post 时，`structured_info` 被硬编码设置为空字符串 `""`
- 可视化脚本查询时要求：`structured_info IS NOT NULL AND structured_info != ''`
- 这会导致**所有 posts 都被过滤掉**（因为 structured_info 总是空字符串）

**代码证据**：
```python
# platform.py - create_post()
post_insert_query = (
    "INSERT INTO post (user_id, content, structured_info, created_at, ...) "
    "VALUES (?, ?, ?, ?, ...)")
self.pl_utils._execute_db_command(
    post_insert_query, (user_id, content, "", current_time, ...),  # structured_info = ""
    commit=True)

# rq3_visualization.py - _load_communication_data()
query = """
    SELECT ...
    WHERE u.role = 'seller' 
      AND p.structured_info IS NOT NULL 
      AND p.structured_info != ''  # 这个条件会过滤掉所有 posts！
"""
```

**解决方案**：修改可视化脚本的查询条件，移除 `structured_info != ''` 的限制，或者改为查询所有 seller posts。

### 3. **Round 过滤的不准确性**

**代码位置**：`visualization/scripts/rq3_visualization.py` - `_load_communication_data()`

**问题**：
- Posts 表没有直接的 `round_number` 字段
- 只能通过 `created_at` 时间戳近似推断 round
- Communication phase 在每个 round 开始时执行，但时间戳可能不准确对应到特定 round

**代码注释**：
```python
# Return all seller posts (round filtering can be improved using action_log)
# For now, return all posts and let the caller handle round-specific filtering
```

**结论**：按 round 查询 communication posts 可能不准确，建议查询所有 posts 然后在应用层过滤。

### 4. **Fake vs Real Channel 的影响**

**代码位置**：`oasis/social_agent/agent_environment.py` - `get_posts_communication_for_env()`

**Fake Channel 模式**：
- Agents 只能看到自己的 posts
- 这可能导致 agents 认为没有其他信息需要分享，从而减少 communication

**Real Channel 模式**：
- Agents 可以看到所有其他 agents 的 posts
- 可能激发更多的 communication 行为

### 5. **第一 Round 的特殊情况**

**代码位置**：`oasis_market/phases.py` - `CommunicationPhase.execute()`

- Seller communication 在每个 round **开始时**执行
- 第一 round 时，sellers 还没有任何市场经验，可能没有信息需要分享
- 后续 rounds 中，sellers 有了更多经验，communication 可能增加

## 建议的修复方案

### 1. 修复可视化脚本的查询条件

**修改** `visualization/scripts/rq3_visualization.py`：

```python
# 移除 structured_info 的限制，查询所有 seller posts
query = """
    SELECT p.post_id, p.user_id, p.content, p.structured_info, p.created_at
    FROM post p
    JOIN user u ON p.user_id = u.user_id
    WHERE u.role = 'seller'
    ORDER BY p.created_at
"""
```

### 2. 改进 Round 过滤逻辑

如果需要按 round 过滤，可以：
- 使用 `action_log` 表来关联 posts 和 rounds
- 或者查询所有 posts，然后在应用层根据时间戳范围过滤

### 3. 添加调试日志

在 `CommunicationPhase` 中添加日志，记录：
- 每个 round 有多少 agents 参与了 communication phase
- 有多少 agents 实际创建了 posts
- 有多少 agents 选择了其他操作（like, quote 等）

## 总结

某些 round 没有 communication posts 是**正常现象**，主要原因包括：

1. ✅ **Agents 的自主决策** - LLM agents 可能选择不创建 post
2. ❌ **查询条件错误** - `structured_info != ''` 过滤掉了所有 posts（需要修复）
3. ⚠️ **Round 过滤不准确** - 时间戳推断可能不准确
4. ℹ️ **Channel 类型影响** - Fake channel 可能减少 communication
5. ℹ️ **Round 阶段影响** - 早期 rounds 可能 communication 较少

**最紧急的修复**：移除可视化脚本中 `structured_info != ''` 的查询限制。

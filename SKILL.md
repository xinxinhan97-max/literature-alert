---
name: setup-literature
description: >-
  This skill should be used when the user asks to set up automated literature alerts,
  "搭建文献推送", "文献推送系统", "每日文献", "自动文献检索", "文献追踪",
  "paper alert", "literature alert", "论文推送", "AI 文献分析",
  asks to create a daily paper recommendation system with AI-powered analysis,
  or wants to do a one-time literature search ("文献检索", "搜论文", "找文献").
  Also trigger when the user wants to "帮我做一个每天自动检索论文的工具".
---

# 搭建自动化文献推送 / 一次性文献检索

为用户生成文献检索系统，支持两种模式：定期推送 or 一次性检索。AI 分析、HTML 报告、期刊 IF 匹配两组共用。

## 核心理念

步骤逐项过，不能跳过。用户说"默认就行"才能跳。可合并的问题一次问完，减少来回。绝不索取 API key、密码等凭据——生成占位符指引用户自己填写。

---

## 步骤 0：选择模式

首先问用户：

> "你想用哪个功能？
> A) 定时文献推送 — 每天自动搜新论文，推送到浏览器/邮件
> B) 一次性文献检索 — 指定检索词和日期范围，搜一次出报告"

选 A → 进入推送流程（步骤 P1-P5）
选 B → 进入检索流程（步骤 S1-S4）

---

## 推送流程（Push Mode）

### 步骤 P1：了解研究方向

请用户描述研究方向。给一个范例：

> "我研究电催化CO₂还原，重点关注Cu基催化剂上的乙烯生成和脉冲电位策略"

接受中英文混合输入。

### 步骤 P2：生成检索词并确认

根据研究方向，为每个方向生成 **L1（精准）和 L2（宽泛）** 两层检索：

- **OpenAlex 查询**：3-5 个英文核心关键词，自然语言格式
- **arXiv 查询**：布尔格式，`all:term AND all:term` 语法，用括号包围

展示给用户确认或修改。顺便问一句要不要开 arXiv（有些领域 arXiv 没用）。

### 步骤 P3：AI 分析设置

| 问题 | 默认值 |
|------|--------|
| 输出语言？（中文 / 英文 / 双语） | 中文 |
| AI 模型？ | DeepSeek（详细选项见下方） |

可选的 AI 模型：

| 选项 | base_url | model | 费用 |
|------|----------|-------|------|
| A) DeepSeek（推荐） | `https://api.deepseek.com/v1` | `deepseek-chat` | ~¥2/月 |
| B) OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | ~¥5/月 |
| C) 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` | ~¥3/月 |
| D) 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | ~¥3/月 |
| E) 不要 AI 分析 | — | — | 免费 |
| F) 其他 OpenAI 兼容 API | 用户提供 | 用户提供 | 不定 |

### 步骤 P4：推送方式

| 问题 | 默认值 |
|------|--------|
| 每周哪几天推送？ | 周一至周五 |
| 每天推送相同内容还是不同？ | 相同 |
| 每天几点推送？ | 08:00 |
| 定时推送 / 开机自启 / 两个都要？ | 两个都要 |
| 要不要邮件推送？ | 否 |

> ⚠️ 提醒：定时推送依赖 Windows 任务计划程序，**需要电脑在设定的时间处于开机状态**。关机错过了，开机自启可以补跑一次。

如果每天不同主题 → 为每天分别生成检索词。
如果要邮件 → 指引用户开 QQ 邮箱 SMTP、生成授权码、填 config.json。不索取授权码。

### 步骤 P5：输出目录

默认 `当前目录/literature_alert/`，通常不改。

---

## 检索流程（Search Mode）

### 步骤 S1：了解研究方向

同 P1。让用户描述，给范例。

### 步骤 S2：检索词 + 检索范围

根据研究方向生成检索词（L1/L2），同 P2。

额外的：

| 问题 | 默认值 |
|------|--------|
| 发表日期范围？ | 最近 30 天 |
| 要搜 arXiv 吗？ | 是 |
| 每层最多返回多少篇？ | 30 篇 |

日期范围支持：
- "最近一周" / "最近一个月" / "最近三个月"
- 具体区间 "2024-01-01 到 2024-06-30"
- "从 2023-01-01 至今"

### 步骤 S3：语言 + AI 模型

同 P3。

### 步骤 S4：输出目录

默认当前目录。

---

## 生成文件（两种模式共用）

### 1. 推送模式：`strategies.json`

```json
{
  "workdays": [0, 1, 2, 3, 4],
  "schedule_time": "08:00",
  "directions": [
    {"id": 1, "name": "用户方向的完整中文名", "name_short": "简短标签", "en_name": "English keywords"}
  ],
  "days": {
    "0": {
      "topic": "中文主题",
      "subtitle": "副标题描述",
      "direction_ids": [1],
      "layers": [
        {"label": "L1 精准检索", "openalex": "core keyword query", "arxiv": "(all:term1 AND all:term2)"},
        {"label": "L2 宽泛检索", "openalex": "broader query", "arxiv": "(all:term1 AND all:term3) OR (all:term2 AND all:term4)"}
      ]
    }
  }
}
```

**规则：**
- `workdays`: 整数数组，0=周一，6=周日
- `directions[].id`: 从 1 开始递增
- `days` 的 key 是工作日数字的字符串
- 如果每天主题相同，`days` 里每天用同一个 topic 和 layers
- `direction_ids` 指向 `directions` 中对应的方向 id
- 每天至少 1 层、最多 3 层检索

### 2. 检索模式：`search_task.json`

```json
{
  "topic": "检索主题",
  "subtitle": "副标题",
  "directions": [
    {"id": 1, "name": "方向全名", "name_short": "标签", "en_name": "English keywords"}
  ],
  "queries": [
    {"label": "L1 精准检索", "openalex": "core query", "arxiv": "(all:term1 AND all:term2)"},
    {"label": "L2 宽泛检索", "openalex": "broader query", "arxiv": "(all:term1 AND all:term3)"}
  ],
  "date_range": {
    "from": "2024-01-01",
    "to": "2024-06-30"
  },
  "max_results_per_query": 30
}
```

`date_range.to` 可省略（搜至今天）。

### 3. `config.json`

```json
{
  "output": {
    "dir": "",
    "language": "zh"
  },
  "schedule": {
    "enabled": false,
    "time": "08:00",
    "auto_start": false
  },
  "email": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender": "YOUR_EMAIL@qq.com",
    "password": "YOUR_SMTP_AUTH_CODE",
    "receiver": "YOUR_EMAIL@qq.com"
  },
  "search": {
    "max_results_per_query": 15,
    "lookback_days": 7,
    "arxiv_timeout": 60,
    "use_semantic_scholar": false
  },
  "ai": {
    "enabled": true,
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "api_key": "YOUR_API_KEY"
  }
}
```

### 4. `literature_alert.py` 和 `ai_analyzer.py`

从 `templates/` 目录复制到输出目录。

### 5. `journal_if.json`

从 templates 目录复制到输出目录。

### 6. `startup.bat`（仅推送模式 + 开机自启）

```batch
@echo off
cd /d "输出目录"
start "" /min python "输出目录\literature_alert.py"
```

快捷方式到 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`。

### 7. Windows 定时任务（仅推送模式 + 定时推送）

```batch
schtasks /create /tn "LiteratureAlert" /tr "python \"输出目录\literature_alert.py\"" /sc daily /st 08:00
```

---

## 生成后指引

### 推送模式

```
系统已搭建完成！文件位置：{输出目录}

下一步：
1. 打开 config.json：
   - 如需邮件推送 → 填 email 部分（QQ邮箱授权码）
   - 如需 AI 分析 → 填 ai.api_key
2. 试跑验证：
   python literature_alert.py --dry-run
3. 正式运行：
   python literature_alert.py

{根据用户选择}：
- 定时推送已创建：每天 {时间}
- 开机自启已设置
- 手动运行

想调整检索词或推送节奏 → 编辑 strategies.json
换 AI 模型或语言 → 编辑 config.json
```

### 检索模式

```
检索配置已生成！文件位置：{输出目录}

1. 打开 config.json 填 ai.api_key（要 AI 分析的话）
2. 运行：
   python literature_alert.py --search search_task.json
3. 浏览器自动打开结果

想调整检索范围或关键词 → 编辑 search_task.json 再跑一次
```

---

## 注意事项

- 绝不索取或记录用户的 API key、授权码等凭据
- 定时任务需要电脑开机，务必提醒用户
- 如果 `journal_if.json` 不存在，从 templates 复制
- 如果用户要用的 AI 模型不在预设列表中，根据用户提供的 base_url 和 model 名称配置即可

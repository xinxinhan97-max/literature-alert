---
name: setup-literature
description: >-
  This skill should be used when the user asks to set up automated literature alerts,
  "搭建文献推送", "文献推送系统", "每日文献", "自动文献检索", "文献追踪",
  "paper alert", "literature alert", "论文推送", "AI 文献分析",
  or asks to create a daily paper recommendation system with AI-powered analysis.
  Also trigger when the user wants to "帮我做一个每天自动检索论文的工具".
---

# 搭建自动化文献推送系统

为用户在其项目目录下生成一套完整的文献推送系统，包含每日自动检索、AI 分析、交互式 HTML 报告。

## 核心理念

只问必须问的，其余默认值补位。绝不索取 API key、密码等凭据——生成占位符指引用户自己填写。

## 对话流程

### 步骤 1：了解研究方向（必填）

请用户描述研究方向。给一个范例让用户知道怎么说：

> "我研究电催化CO₂还原，重点关注Cu基催化剂上的乙烯生成和脉冲电位策略"

接受中英文混合输入。

### 步骤 2：生成检索词并确认

根据研究方向，为每个方向生成 **L1（精准）和 L2（宽泛）** 两层检索：

- **OpenAlex 查询**：3-5 个英文核心关键词，自然语言格式
- **arXiv 查询**：布尔格式，`all:term AND all:term` 语法，用括号包围

展示给用户确认或修改。

### 步骤 3：确认推送节奏

| 问题 | 默认值 |
|------|--------|
| 每周哪几天推送？ | 周一至周五 |
| 每天推送相同内容还是不同？ | 相同 |

如果用户需要每天不同主题，为每天分别生成检索词。

### 步骤 4：选择 AI 分析模型

| 选项 | base_url | model | 费用 |
|------|----------|-------|------|
| A) DeepSeek（推荐） | `https://api.deepseek.com/v1` | `deepseek-chat` | ~¥2/月 |
| B) OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | ~¥5/月 |
| C) 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` | ~¥3/月 |
| D) 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | ~¥3/月 |
| E) 不要 AI 分析 | — | — | 免费 |
| F) 其他 OpenAI 兼容 API | 用户提供 | 用户提供 | 不定 |

### 步骤 5：邮件推送？（默认：否）

如果用户需要邮件推送，指引用户：
1. 登录 QQ 邮箱 → 设置 → 账户 → 开启 POP3/SMTP 服务
2. 生成授权码
3. 填入 `config.json` 的 `email` 部分

不索取授权码，只在对话中指引。

### 步骤 6：开机自启动？（默认：是）

如果是 → 创建 `startup.bat` 并添加快捷方式到 Windows 启动文件夹。
如果否 → 跳过。

### 步骤 7：输出目录（默认：当前目录/literature_alert/）

---

## 生成文件

### 1. `strategies.json`

```json
{
  "workdays": [0, 1, 2, 3, 4],
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

### 2. `literature_alert.py` 和 `ai_analyzer.py`

从 `templates/` 目录复制到输出目录。

### 3. `config.json`

从 `templates/config.json` 复制，包含所有占位符。

### 4. `journal_if.json`

从当前 skill 所在位置（`E:\硕士\literature_alert\journal_if.json`）复制到输出目录。如源文件不存在，创建空 `{}` 并提示用户稍后手动复制。

### 5. `startup.bat`（仅当用户选择开机自启）

```batch
@echo off
cd /d "输出目录"
start "" /min python "输出目录\literature_alert.py"
```

然后创建快捷方式到 `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`。

---

## 生成后指引

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

以后每次开机自动运行，浏览器弹出文献报告。
想调整检索词或推送节奏 → 编辑 strategies.json
想换 AI 模型 → 编辑 config.json 的 ai 部分
```

## 注意事项

- 绝不索取或记录用户的 API key、授权码等凭据
- 如果 `journal_if.json` 源文件不可用，创建空文件并说明
- 如果用户要用的 AI 模型不在预设列表中，根据用户提供的 base_url 和 model 名称配置即可

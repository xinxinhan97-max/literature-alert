# 📚 Literature Alert — 自动化文献推送系统

一键搭建属于你自己的每日文献推送。检索 → AI 分析 → 交互式报告，开机自动运行。

[English](#english) | [中文](#chinese)

---

## 中文

### 这是什么？

每天早上开机，浏览器自动弹出一份文献报告：最近 7 天的最新论文，按你的研究方向打分排序，每篇附带中文翻译、创新点提炼和可借鉴之处。标记已读/不读，写笔记，导出日志。

**不用懂 Python，不用配服务器。** 在 Claude Code 里输入 `/setup-literature`，聊 5 分钟就搭好。

### 快速开始

```bash
# 1. 在 Claude Code 中
/setup-literature

# 2. 跟着对话走（只需要描述你的研究方向）

# 3. 如果要用 AI 分析，去 platform.deepseek.com 申请 API Key（¥2/月）
#    填入生成的 config.json

# 4. 试跑
python literature_alert.py --dry-run

# 5. 正式运行
python literature_alert.py
```

### 你能得到什么

- 🔍 每天自动检索 OpenAlex（2.5 亿篇论文）
- 📊 自动匹配期刊影响因子（10200 本期刊）
- 🤖 AI 分析：评分、课题匹配、创新点、可借鉴之处
- 📝 逐句中文翻译（忠实原文，不概括）
- 📈 按相关度从高到低排序
- ✅ 浏览器交互：标记已读/不读、写笔记、导出 Markdown 日志
- 📧 可选邮件推送（QQ 邮箱 SMTP）
- 🚀 开机自动运行（Windows 启动文件夹）

### 支持的 AI 模型

| 模型 | 月费（估） |
|------|:--:|
| DeepSeek（推荐） | ~¥2 |
| OpenAI GPT-4o-mini | ~¥5 |
| 智谱 GLM-4-Flash | ~¥3 |
| 通义千问 Qwen-Plus | ~¥3 |
| 本地 Ollama | 免费 |
| 不用 AI | 免费 |

### 文件结构

```
literature_alert/
├── literature_alert.py    # 主脚本
├── ai_analyzer.py         # AI 分析模块
├── config.json            # 配置（API Key、邮箱等）
├── strategies.json        # 检索策略（你的研究方向）
├── journal_if.json        # 期刊影响因子对照表
└── literature_MMDD.html   # 每日生成的报告
```

### 依赖

仅需 Python 3.9+，零外部 pip 包（全部标准库）。

### 手动安装（不用 Claude Code）

```bash
git clone https://github.com/xinxinhan/literature-alert.git
cd literature-alert/templates

# 1. 编辑 strategies.json（你的研究方向）
# 2. 编辑 config.json（API Key 等）
# 3. 复制所有文件到你想要的工作目录
# 4. 运行
python literature_alert.py --dry-run
```

### 赞助 / Sponsor

如果这个项目对你有帮助，欢迎请我喝杯咖啡 ☕

<div align="center">
  <table>
    <tr>
      <td align="center"><b>支付宝</b></td>
      <td align="center"><b>微信</b></td>
    </tr>
    <tr>
      <td><img src="支付宝收款码.jpg" width="200" alt="支付宝"></td>
      <td><img src="微信收款码.jpg" width="200" alt="微信"></td>
    </tr>
  </table>
</div>

---

## English

### What is this?

A fully automated daily literature alert system. Every morning when you turn on your computer, a browser tab opens with freshly published papers in your field, scored and analyzed by AI, with Chinese translations, innovation highlights, and actionable takeaways.

### How it works

1. **Search** — Queries OpenAlex (250M+ papers) using your custom search terms
2. **Match IF** — Automatically looks up journal impact factors (10,200 journals)
3. **AI Analysis** — Scores relevance, matches to your sub-fields, extracts innovation points
4. **Generate Report** — Interactive HTML with read/skip/note-taking, sortable by relevance
5. **Email (optional)** — Sends a read-only version to your inbox

### Install via Claude Code

```
/setup-literature
```

### Install manually

```bash
git clone https://github.com/xinxinhan/literature-alert.git
cd literature-alert/templates
# Edit strategies.json and config.json with your settings
python literature_alert.py --dry-run
```

### Zero dependencies

Uses only Python standard library — no pip installs, no API wrappers, no frameworks.

### Sponsor

If this project helps you, buy me a coffee ☕

<div align="center">
  <table>
    <tr>
      <td align="center"><b>Alipay</b></td>
      <td align="center"><b>WeChat</b></td>
    </tr>
    <tr>
      <td><img src="支付宝收款码.jpg" width="200" alt="Alipay"></td>
      <td><img src="微信收款码.jpg" width="200" alt="WeChat"></td>
    </tr>
  </table>
</div>

### License

MIT

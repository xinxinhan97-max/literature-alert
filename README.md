# Literature Alert

我每天开机第一件事就是扫一眼今天有什么新论文。但手工搜太费时间了，所以写了这个东西。

你告诉它你的研究方向，它会每天自动检索最新论文，AI 帮你打分、匹配子课题、翻译成中文、标出创新点。浏览器里打开就能标记哪些读了、哪些跳过、顺手写几句笔记，最后导出一份 Markdown 日志。

在 Claude Code 里输 `/setup-literature`，聊几句就搭好了。不用懂 Python，不用买服务器。

---

## 怎么用

### Claude Code 一键部署

```
/setup-literature
```

跟着对话走，描述你的研究方向就行。AI 模型用 DeepSeek 的话，一个月大概花 2 块钱。

### 手动安装

```bash
git clone https://github.com/xinxinhan97-max/literature-alert.git
cd literature-alert/templates
# 打开 strategies.json 写上你的研究方向
# 打开 config.json 填 API Key（如果要用 AI 分析）
python literature_alert.py --dry-run   # 试跑
python literature_alert.py             # 正式运行
```

## 它做了什么

- 每天检索最近一周的新论文（OpenAlex，2.5 亿篇）
- AI 给你的课题打分（1-5 星），匹配到你具体的子方向
- 每篇论文逐句翻译（中文 / 英文 / 双语，你自己选）
- 提炼创新点、方法、关键指标，写一句"对你有啥用"
- 自动标上期刊影响因子和 Q 分区
- 浏览器交互：已读 / 不读 / 写笔记 / 导出日志
- 可以顺便发一封邮件给你（用的 QQ 邮箱 SMTP）
- 定时推送 + 开机自启，不用管
- 输出路径、推送时间、语言都可以自己定

## 支持的 AI 模型

DeepSeek、OpenAI、智谱、通义千问、本地 Ollama 都行。不用 AI 分析也可以，纯检索 + 翻译。

## 环境要求

Python 3.9 以上，不需要安装任何第三方包。到哪台电脑上都能跑。

---

## English

I built this because I got tired of manually searching for papers every morning.

Describe your research area, and it fetches the latest papers daily. An AI reads each one, scores how relevant it is to your specific sub-topics, translates the abstract into Chinese, and pulls out what's new and what you can learn from it. Results open in your browser — you can mark papers read or skip, jot down notes, and export everything as a Markdown reading log.

Type `/setup-literature` in Claude Code and you're done in a few minutes. No Python knowledge needed, no server to maintain.

### How it works

- Searches OpenAlex (250M papers) for the past week
- AI scores relevance to your sub-fields and highlights innovations
- Abstract translation in Chinese, English, or bilingual (your choice)
- Interactive HTML with read/skip/notes/export
- Journal impact factor lookup (10,200 journals)
- Optional email digest
- Scheduled daily push + auto-start on boot
- Customizable output path, push time, and language

### Install

```
/setup-literature
```

Or manually:

```bash
git clone https://github.com/xinxinhan97-max/literature-alert.git
cd literature-alert/templates
python literature_alert.py --dry-run
```

### AI models supported

DeepSeek (recommended), OpenAI, Zhipu GLM, Qwen, local Ollama — or skip AI entirely. Only costs about $0.3/month with DeepSeek.

### Requirements

Python 3.9+. Zero pip dependencies.

---

## Sponsor

如果这个东西帮你省了时间，可以请我喝杯咖啡。

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

## License

MIT

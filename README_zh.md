# 🚀 pageIndex-rag-chat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**基于 ReAct 范式构建的 Agentic RAG Web UI 系统，可视化文档的检索与推理过程**

## 💡 为什么做这个项目？

[PageIndex](https://github.com/VectifyAI/PageIndex) 优雅地解决了长文本的结构化提取问题，为文档生成了完美的全局大纲（Table of Contents）。**但是，它的推理引擎部分并没有完全开源。**

本项目 **PageIndex-Reasoner** 正是为了补齐这最后一块拼图！
传统的 RAG 系统往往采用“无脑切块 + 向量检索”的方式，极易在长文档中丢失全局上下文（Lost in the middle）。本项目引入了 **Thought-Judge 双路智能体架构**，让大模型像人类阅读书籍一样：**先看目录大纲 ➡️ 锁定相关章节 (node_id) ➡️ 精准提取文本 ➡️ 评估提取结果 ➡️ 整合最终回答**。

## ✨ 核心特性

- 🗺️ **TOC-Driven Navigation (大纲驱动导航)**: 摒弃盲目的向量匹配，Agent 直接阅读全局大纲，基于逻辑关联精准定位目标章节。
- 🕵️‍♂️ **ReAct 思考引擎 (Thought-Agent)**: 赋予模型自主决策能力，自主决定需要调用哪个 `node_id`，按需加载，大幅节省 Token 开销。
- ⚖️ **动态评估与反思 (Judge-Agent)**: 独创评估闭环。每次提取文本后，自动评估信息是否“有用”，动态构建高质量的局部知识库，过滤无关噪音。
- 🔌 **极简接入 (Plug & Play)**: 原生适配 PageIndex 输出的 `_structure.json` 格式。代码轻量，开箱即用，目前已无缝对接阿里云百炼 (Qwen 模型)。

## 🛠️ 核心架构图

```text
User Query 
   │
   ▼
[ 加载文档大纲 TOC ] ──────┐
   │                       │
   ▼                       ▼
Thought-Agent ◄───── [ 当前知识库 ]
   │  (决定下一步行动)        ▲
   ▼                       │
调用工具 (get_texts)       │
   │                       │
   ▼                       │
Judge-Agent ───────────────┘
  (评估结果是否有用，并总结经验)
   │
   ▼ (当收集到足够信息时)
调用工具 (get_answer) 
   │
   ▼
生成最终回答 🚀
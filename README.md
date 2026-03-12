<div align="right">
  <strong>English</strong> | <a href="README_zh.md">简体中文</a>
</div>

# 🚀 pageIndex-rag-chat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**A complete RAG Chat Web UI system built on PageIndex! Powered by the ReAct paradigm, it combines TOC (Table of Contents) navigation with an explicit reasoning process for an intelligent and transparent document Q&A experience.**

## 💡 Why this project?

[PageIndex](https://github.com/VectifyAI/PageIndex) elegantly solves the structured extraction of long texts, generating perfect global outlines (Table of Contents) for documents. **However, its reasoning engine was not open-sourced.**

**PageIndex-Reasoner** was born to complete this missing puzzle piece! 
Traditional RAG systems often rely on "blind chunking + vector search," which easily leads to losing the global context in long documents (Lost in the Middle). This project introduces a **Thought-Judge dual-agent architecture**, allowing the LLM to read documents like a human: **Review the TOC ➡️ Locate relevant chapters (node_id) ➡️ Precisely extract text ➡️ Evaluate the results ➡️ Synthesize the final answer.**

## ✨ Key Features

- 🗺️ **TOC-Driven Navigation**: Say goodbye to blind vector matching. The Agent reads the global TOC directly, locating target chapters based on logical correlation rather than mere semantic similarity.
- 🕵️‍♂️ **ReAct Engine (Thought-Agent)**: Empowers the model with autonomous decision-making. It decides which `node_id` to call and loads data on demand, significantly saving Token costs.
- ⚖️ **Dynamic Evaluation & Reflection (Judge-Agent)**: An innovative evaluation loop. After each text extraction, it automatically evaluates whether the information is "useful" and dynamically builds a high-quality local knowledge base, filtering out irrelevant noise.
- 🔌 **Plug & Play**: Natively supports the `_structure.json` format output by PageIndex. Lightweight and ready to use out of the box. Currently seamlessly integrated with Qwen via DashScope.

## 🛠️ Architecture

```text
User Query 
   │
   ▼
[ Load Document TOC ] ────────┐
   │                          │
   ▼                          ▼
Thought-Agent ◄───── [ Current Knowledge Base ]
   │  (Decides next action)   ▲
   ▼                          │
Call Tool (get_texts)         │
   │                          │
   ▼                          │
Judge-Agent ──────────────────┘
  (Evaluates usefulness & summarizes)
   │
   ▼ (When enough info is gathered)
Call Tool (get_answer) 
   │
   ▼
Generate Final Answer 🚀
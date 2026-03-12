# pageIndex-rag-chat
基于 pageIndex 以ReAct范式构建的 Agentic RAG Web UI 系统，可视化文档检索与推理过程，效果还原度 95%+。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
## 结果展示

复现效果
![效果对比 1](pic/img1.png)

![效果对比 2](pic/img2.png)
官方效果
![效果对比 3](pic/img3.png)

## 快速开始
```
安装依赖
pip install -r requirements.txt
启动服务
python main.py
```
浏览器中访问http://127.0.0.1:8000/

## ✨ 核心特性
- 🚀 **fastapi**：服务基于fastapi构建，可加入到自己的应用中
- 🗺️ **大纲驱动导航**：摒弃盲向量匹配，Agent 读取全局大纲，基于逻辑关联精准定位目标章节
- 🕵️‍♂️ **ReAct 思考引擎**：赋予模型自主决策能力，按需加载内容，大幅降低 Token 开销
- ⚖️ **动态评估反思**：提取文本后自动评估有效性，动态构建高质量局部知识库，过滤无关噪音
- 🔌 **极简即插即用**：原生适配 PageIndex 输出的 `_structure.json` 格式，轻量开箱，兼容各类 OpenAI 兼容 API

注意：本项目对于pageIndex核心代码进行了修改，适配兼容openai的接口,在.env中配置(原项目只支持chatgpt-api)
```text
.env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=model_name
OPENAI_BASE_URL=base_url

```
## 🛠️ 核心架构
```text
用户查询
   │
   ▼
[加载文档大纲 TOC] ──────┐
   │                       │
   ▼                       ▼
Thought-Agent ◄───── [当前知识库]
   │ (自主决策下一步行动)      ▲
   ▼                       │
调用工具 (get_texts)       │
   │                       │
   ▼                       │
Judge-Agent ───────────────┘
  (评估结果有效性，总结经验)
   │
   ▼ (信息足够时触发)
调用工具 (get_answer)
   │
   ▼
生成最终回答
```
## 📌 未来实现
- [ ] 支持多文档问答能力
- [ ] 封装为 MCP 接口
- [ ] 集成数据库存储能力
- [ ] 对接 Ollama/VLLM，实现本地全量部署


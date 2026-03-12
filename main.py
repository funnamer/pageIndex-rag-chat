import os
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from agent import react_agent_system_stream

app = FastAPI(title="Agentic RAG API")

# 确保目录存在
os.makedirs("data", exist_ok=True)
os.makedirs("results", exist_ok=True)

# 挂载模板目录
templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    query: str
    doc_name: str


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染主前端页面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/docs")
async def get_docs():
    """获取所有已解析的文档列表"""
    docs = []
    if os.path.exists("results"):
        for f in os.listdir("results"):
            if f.endswith("_structure.json"):
                docs.append(f.replace("_structure.json", ""))
    return {"docs": docs}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """处理文件上传并触发结构化解析"""
    file_path = os.path.join("data", file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    ext = file.filename.split('.')[-1].lower()
    cmd = ["python", "run_pageindex.py"]
    if ext == 'pdf':
        cmd.extend(["--pdf_path", file_path])
    elif ext in ['md', 'markdown']:
        cmd.extend(["--md_path", file_path])
    else:
        return {"status": "error", "message": "仅支持 PDF 或 Markdown 文件"}

    # 异步执行耗时的处理脚本，避免阻塞主线程
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return {"status": "success", "message": f"{file.filename} 解析成功！"}
    else:
        return {"status": "error", "message": f"解析失败: {stderr.decode()}"}


@app.post("/api/chat")
async def chat_stream(req: ChatRequest):
    """处理流式对话请求 (SSE)"""

    async def event_generator():
        # 遍历我们在 agent.py 中写的生成器，把每一步的状态转为 SSE 格式推送给前端
        for step in react_agent_system_stream(req.query, req.doc_name):
            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            # 微小延迟，防止阻塞事件循环
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    # 运行命令: python main.py 或者 uvicorn main:app --reload
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
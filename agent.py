import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# 导入你写好的真实工具函数
from utils import get_structure as fetch_structure, get_texts_by_node_ids

# 1. 初始化客户端 (使用百炼 DashScope)
client = OpenAI(
    api_key=os.environ.get("DASHSCOPE_API_KEY", "你的阿里云API-KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)


# ---------------- 核心 LLM 调用 ----------------
def call_qwen(prompt: str, is_final: bool = False) -> str:
    """调用 qwen3-plus 模型。is_final 控制系统提示词"""
    try:
        sys_prompt = "你是一个严谨的AI助手，请严格按照要求的XML标签格式输出，不要输出任何多余的寒暄或解释。"
        if is_final:
            sys_prompt = "你是一个专业的AI助手，请根据提供的上下文，准确、详细地回答用户的问题。"

        response = client.chat.completions.create(
            model="qwen3-max",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ [LLM API 调用失败]: {e}")
        return ""


# ---------------- 工具与执行器 ----------------
def execute_tool(tool_name: str, parameters_str: str, doc_name: str) -> str:
    """真实环境执行器：调用 utils.py 中的工具"""
    print(f"  🔧 [Executor] 正在执行: {tool_name}, 参数: {parameters_str}, 文档: {doc_name}")

    params = {}
    if parameters_str.strip():
        try:
            params = json.loads(parameters_str)
        except json.JSONDecodeError:
            return f"系统报错: 提供的参数不是合法的 JSON 格式: {parameters_str}"

    try:
        # 注意：这里去掉了 get_structure 工具，只保留了 get_texts
        if tool_name == "get_texts":
            node_ids = params.get("node_ids", [])
            if not isinstance(node_ids, list):
                return '系统报错: 参数必须包含 "node_ids" 键，且值为整数列表，例如 {"node_ids": [1, 2]}'

            node_ids = [int(n) for n in node_ids]
            result = get_texts_by_node_ids(doc_name, node_ids)
            return json.dumps(result, ensure_ascii=False)

        else:
            return f"系统报错: 找不到名为 '{tool_name}' 的工具，请检查工具名称。"

    except Exception as e:
        return f"系统报错: 工具执行出现异常: {str(e)}"


# ---------------- 工具函数与解析器 ----------------
def parse_tags(text: str, tags: list) -> dict:
    """利用正则从模型输出中提取 XML 标签内容"""
    result = {}
    for tag in tags:
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        result[tag] = match.group(1).strip() if match else ""
    return result


# ---------------- 核心 Agent 逻辑 ----------------
def react_agent_system(query: str, doc_name: str, max_iterations=5):
    knowledge_base = []
    useful_node_ids = set()  # 全局存储有用的 node_id，使用 set 去重

    print(f"\n{'=' * 50}")
    print(f"🎯 收到任务 Query: {query}")
    print(f"📄 目标文档: {doc_name}")
    print(f"{'=' * 50}\n")

    # ---------------- 1. 初始化：预先获取并加载大纲 ----------------
    print("📚 [系统] 正在提取并加载文档全局大纲...")
    try:
        raw_structure = fetch_structure(doc_name)
        structure_context = json.dumps(raw_structure, ensure_ascii=False)
        print("📚 [系统] 大纲加载完毕。")
    except Exception as e:
        print(f"❌ [系统报错] 无法获取文档大纲: {e}")
        return "初始化失败"

    for i in range(max_iterations):
        print(f"🔄 --- [Iteration {i + 1}/{max_iterations}] ---")

        kb_text = "\n".join([f"{idx + 1}. {item}" for idx, item in enumerate(knowledge_base)])
        if not kb_text:
            # 第一次执行的提示词改变：引导它直接看大纲并使用 get_texts
            kb_text = "暂无执行记录。你是第一次执行，请先仔细阅读上方提供的【文档大纲】，寻找与用户问题相关的 node_id，并调用 get_texts 获取文本。"

        thought_prompt = f"""你是一个具备逻辑推理能力的智能助手 (Thought-Agent)。
你的目标是解答用户的 Query。你可以使用工具，并参考当前的知识库（你之前尝试过的行动和结果评估）。

【文档大纲】(全局参考)
{structure_context}

【用户 Query】
{query}

【当前知识库】(你的历史行动和排错记录)
{kb_text}

【可用工具】
1. get_texts: 根据 node_id 获取具体章节的详细文本。参数为 node_id 列表，例如：<parameter>{{"node_ids": [101, 105]}}</parameter>
2. get_answer: 收集到足够信息可以回答用户时调用。参数请留空，例如：<parameter></parameter>

【输出格式要求】 (请严格输出以下 XML 标签，不要包含其他内容)
<think>分析文档大纲和当前知识库，决定下一步该调用哪个工具，比如 :get_texts</think>
<tool>你要调用的工具名称</tool>
<parameter>传递给工具的 JSON 格式参数(如无参数则留空)</parameter>
"""

        thought_response = call_qwen(thought_prompt)
        t_parsed = parse_tags(thought_response, ["think", "tool", "parameter"])

        t_think = t_parsed.get("think", "解析失败")
        t_tool = t_parsed.get("tool", "无工具")
        t_param = t_parsed.get("parameter", "")

        print(f"🧠 [Thought-Agent]")
        print(f"   ► 思考 (Think): {t_think}")
        print(f"   ► 决策 (Tool):  {t_tool}")
        print(f"   ► 参数 (Param): {t_param}")

        # ---------------- 最终答案生成逻辑 ----------------
        if t_tool == "get_answer":
            if not useful_node_ids:
                return "未能收集到任何有用的文档信息，无法给出答案。"

            print(f"\n🚀 [准备答复] 正在提取所有有用节点 {list(useful_node_ids)} 的内容进行最终总结...")

            final_context_data = get_texts_by_node_ids(doc_name, list(useful_node_ids))
            final_context_str = json.dumps(final_context_data, ensure_ascii=False)

            # ========== 🚀 加这两行调试代码 ==========
            print(f"\n[Debug] 最终组装的文本长度: {len(final_context_str)}")
            print(f"[Debug] 最终文本预览:\n{final_context_str[:300]}...\n")
            # ========================================

            # 建议稍微放宽最终的 Prompt，允许大模型进行中英文意译
            final_prompt = f"""请基于以下检索到的文档内容，详细回答用户的问题。
        文档可能是英文的，请自动翻译并总结。如果检索到的内容完全与问题无关，再说明“文档中未提及”。

        【用户问题】
        {query}

        【文档提取内容】
        {final_context_str}
        """
            # 3. 调用 LLM 生成最终答案
            final_answer = call_qwen(final_prompt, is_final=True)
            print(f"\n✅ [任务完成] 最终答案:\n{final_answer}\n")
            return final_answer

        # ---------------- 执行与评估逻辑 ----------------
        exec_result = execute_tool(t_tool, t_param, doc_name)

        judge_prompt = f"""你是一个评估专家 (Judge-Agent)。你的任务是评估 Thought-Agent 上一步行动的有效性，并为它总结经验。

【用户 Query】
{query}
【Thought-Agent 刚刚的思考】
{t_think}
【Thought-Agent 刚才的行动】
使用的工具: {t_tool}
传入的参数: {t_param}

【工具返回的原始结果】
{exec_result}

【输出格式要求】(请严格输出以下 XML 标签)
<think>评估执行结果是否有用，是否获取到了解决当前问题所需的数据，并说明原因。</think>
<conclusion>有用 or 无用</conclusion>
<summary>简明扼要地总结此次行动获取到的核心信息。内容里包含什么信息，是否能回答Thought-Agent思考的内容</summary>
"""

        judge_response = call_qwen(judge_prompt)
        j_parsed = parse_tags(judge_response, ["think", "conclusion", "summary"])

        j_think = j_parsed.get("think", "解析失败")
        j_conclusion = j_parsed.get("conclusion", "无用")
        j_summary = j_parsed.get("summary", "未能生成总结")

        print(f"⚖️  [Judge-Agent]")
        print(f"   ► 评估 (Think): {j_think}")
        print(f"   ► 结论 (Conclusion): {j_conclusion}")
        print(f"   ► 总结 (Summary): {j_summary}")

        # ---------------- 核心更新逻辑：收集 useful_node_ids ----------------
        if "有用" in j_conclusion and t_tool == "get_texts":
            try:
                params_dict = json.loads(t_param)
                ids_to_add = params_dict.get("node_ids", [])
                if isinstance(ids_to_add, list):
                    useful_node_ids.update([int(n) for n in ids_to_add])
                    print(f"   📌 [系统笔记] 将节点 {ids_to_add} 加入最终阅读列表。")
            except Exception as e:
                print(f"   ⚠️ [解析参数警告] 无法从参数中提取 node_ids: {e}")

        # 每次 Judge 评估完，都将 Summary 加入知识库供下一次循环使用
        knowledge_base.append(j_summary)
        print("-" * 50 + "\n")

    print("⚠️ 达到最大循环次数 (5次)，强制终止，未能完成任务。")
    return "未能得出结论"


if __name__ == "__main__":
    test_query = "各模型在 SWE-rebench的表现如何"

    # ⚠️ 提示：在你的 utils.py 中，它会自动加上 "_structure.json" 的后缀
    # 所以如果你本地的文件名是 "GLM5-report_structure.json"，这里只需传入 "GLM5-report"
    target_doc_name = "GLM5-report"

    react_agent_system(test_query, target_doc_name)
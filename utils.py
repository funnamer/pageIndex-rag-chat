import json
from typing import List, Dict, Any
from pathlib import Path


def get_structure(doc_name: str) -> List[Dict[str, Any]]:
    """
    从 {doc_name}_structure.json 文件中获取章节结构信息。
    
    规则：
    - 一级列表保留 title、node_id 和 summary
    - 递归的 nodes（子节点）只保留 title 和 node_id
    
    Args:
        doc_name: 文档名称（不包含扩展名）
    
    Returns:
        包含章节信息的列表，按照层级结构组织
    """
    def process_node(node: Dict[str, Any], is_top_level: bool = False) -> Dict[str, Any]:
        """
        处理单个节点，根据是否为顶层决定保留哪些字段
        
        Args:
            node: 原始节点字典
            is_top_level: 是否为顶层节点
        
        Returns:
            处理后的节点字典
        """
        if is_top_level:
            # 顶层节点保留 title、node_id 和 summary
            filtered_item = {
                "title": node.get("title"),
                "node_id": node.get("node_id"),
                "summary": node.get("summary")
            }
        else:
            # 子节点只保留 title 和 node_id
            filtered_item = {
                "title": node.get("title"),
                "node_id": node.get("node_id")
            }
        
        # 递归处理嵌套的 nodes
        if "nodes" in node:
            filtered_item["nodes"] = [
                process_node(child_node, is_top_level=False)
                for child_node in node["nodes"]
            ]
        
        return filtered_item
    
    # 构建文件路径
    data_dir = Path(__file__).parent / "results"
    structure_file = data_dir / f"{doc_name}_structure.json"
    
    # 读取 JSON 文件
    with open(structure_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 抽取 structure 字段并处理
    structure_list = data.get("structure", [])
    result = [
        process_node(item, is_top_level=True)
        for item in structure_list
    ]
    
    return result


def get_texts_by_node_ids(doc_name: str, node_ids: List[int]) -> List[Dict[str, Any]]:
    """
    根据传入的 node_ids 列表，从 {doc_name}_structure.json 文件中查找对应的节点，
    并返回包含 node_id 和 text 的 JSON 结果。
    
    Args:
        doc_name: 文档名称（不包含扩展名）
        node_ids: 需要查找的 node_id 列表（整数列表）
    
    Returns:
        包含 node_id 和 text 的字典列表，每个元素格式为：{"node_id": xxx, "text": "..."}
    """
    def find_node_by_id(node: Dict[str, Any], target_id: int) -> Dict[str, Any] | None:
        """
        递归查找具有指定 node_id 的节点
        
        Args:
            node: 当前节点字典
            target_id: 目标 node_id
        
        Returns:
            找到的节点（包含 node_id 和 text），如果未找到则返回 None
        """
        current_node_id = node.get("node_id")
        
        # 将 node_id 转换为整数进行比较
        if current_node_id is not None and int(current_node_id) == target_id:
            return {
                "node_id": current_node_id,
                "text": node.get("text", "")
            }
        
        # 递归搜索子节点
        if "nodes" in node:
            for child_node in node["nodes"]:
                result = find_node_by_id(child_node, target_id)
                if result is not None:
                    return result
        
        return None
    
    # 构建文件路径
    data_dir = Path(__file__).parent / "results"
    structure_file = data_dir / f"{doc_name}_structure.json"
    
    # 读取 JSON 文件
    with open(structure_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 抽取 structure 字段
    structure_list = data.get("structure", [])
    
    # 查找所有匹配的节点
    results = []
    found_node_ids = set()  # 用于去重
    
    for node_id in node_ids:
        # 遍历所有顶层节点进行查找
        for top_node in structure_list:
            result = find_node_by_id(top_node, node_id)
            if result is not None and result["node_id"] not in found_node_ids:
                results.append(result)
                found_node_ids.add(result["node_id"])
                break  # 找到后跳出当前 node_id 的搜索
    
    return results


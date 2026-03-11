from utils import get_structure, get_texts_by_node_ids

# 获取结构信息（不包含 text 字段）
structure = get_structure("GLM5-report")

# print(structure)
# 获取第 1、3、5 页的原始内容
results = get_texts_by_node_ids("GLM5-report", [0, 1, 2])
print(results)
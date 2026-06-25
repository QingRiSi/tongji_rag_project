import sys
import csv
import json

# 确保脚本能找到后端 app 模块
sys.path.append('/app')

from app.components import VectorRetriever

print("正在初始化阿里云大模型向量接口...")
try:
    retriever = VectorRetriever()
except Exception as e:
    print(f"初始化失败，请检查 .env 中的 API Key 是否正确: {e}")
    sys.exit(1)

# 准备张三的原始数据
raw_data = [
    {
        "text": "张三校园卡当前余额为 125.5 元。",
        "source": "学生一卡通系统",
        "dept_id": "CS",
        "user_id": "1"
    }
]

# 导出路径
output_csv_path = "/app/scripts/milvus_exports/rag_person_info.csv"

print(f"开始生成向量并写入文件: {output_csv_path}")

try:
    # 强制使用 utf-8 编码打开文件
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as f:
        # 定义列名，注意必须包含 vector 字段
        fieldnames = ['vector', 'text', 'source', 'dept_id', 'user_id']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for i, row in enumerate(raw_data):
            print(f"正在处理第 {i+1} 条数据...")
            
            # 调用大模型生成向量列表 (如 [0.012, -0.045, ...])
            vector_list = retriever.embedder.embed_query(row["text"])
            
            # 将 List 转换为 JSON 格式的字符串存入 CSV，适配 Milvus 导入脚本
            row["vector"] = json.dumps(vector_list)
            
            writer.writerow(row)

    print("✅ 向量生成完毕！CSV 文件已成功更新，并包含 vector 参数。")
except Exception as e:
    print(f"❌ 发生错误: {e}")
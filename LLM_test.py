# -*- coding: utf-8 -*-
import json
import time
from datetime import datetime
import pandas as pd
from openai import OpenAI

########################
# 配置不同模型的 KEY
########################
MODEL_KEYS = {
    "deepseek": {
        "api_key": "your api_key",
        "base_url": "https://api.deepseek.com/v1"
    },
    "glm": {
        "api_key": "your api_key",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/"
    },
    "qwen": {
        "api_key": "your api_key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "wenxin": {
        "api_key": "your api_key",
        "base_url": "https://aistudio.baidu.com/llm/lmapi/v3"
    }
}

########################
# 通用 Prompt
########################
SYSTEM_PROMPT = """您是一个船舶意图分析器，请严格根据以下规则判断：
1. 找出句子中与输入船名最相似的船舶（考虑中文、拼音、英文大小写、数字差异）。
2. 如果该船舶明确表示要进入黄浦江（包括关键词如"黄浦江"、"张华浜"、"黄浦江内一些码头与泊位"等），返回 {"意图":-1}
3. 其他所有情况（包括其他目的地、无法判断、无关内容），返回 {"意图":0}

输出要求：
- 只输出 JSON 格式：{"意图":0或-1}
- 不要包含任何额外解释或文本
"""

########################
# 通用调用（OpenAI兼容）
########################
def run_openai_compatible(sentence, ship_name, config, model_name):
    start_time = time.time()
    start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"句子: {sentence}\n船名: {ship_name}"}
        ],
        temperature=0.0,
        max_tokens=50,
        response_format={"type": "json_object"}
    )

    end_time = time.time()
    end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed = round(end_time - start_time, 3)

    try:
        result = json.loads(completion.choices[0].message.content)
        intent = result.get("意图", 0)
    except Exception:
        intent = 0

    return {
        "sentence": sentence,
        "ship_name": ship_name,
        "意图": intent,
        "开始时间": start_str,
        "结束时间": end_str,
        "耗时秒": elapsed
    }

########################
# 主调度函数
########################
def extract_ship_intent(sentence, ship_name, model_type="qwen"):
    try:
        if model_type not in MODEL_KEYS:
            raise ValueError(f"不支持的模型类型: {model_type}")
        # 对应模型名称可自定义
        model_name_map = {
            "deepseek": "deepseek-chat",
            "glm": "glm-4-air",
            "qwen": "qwen3-coder-plus",
            "wenxin": "ernie-4.5-turbo-vl"
        }
        return run_openai_compatible(sentence, ship_name, MODEL_KEYS[model_type], model_name_map[model_type])
    except Exception as e:
        print(f"模型 {model_type} 调用失败: {e}")
        return {"sentence": sentence, "ship_name": ship_name, "意图": 0, "开始时间": "", "结束时间": "", "耗时秒": 0}

########################
# Excel 批量处理
########################
def process_excel(input_file, output_file, model_type="qwen"):
    df = pd.read_excel(input_file)
    if not {"sentence", "ship_name"}.issubset(df.columns):
        raise ValueError("Excel 必须包含列名 'sentence' 和 'ship_name'")

    results = []
    for s, name in zip(df["sentence"], df["ship_name"]):
        res = extract_ship_intent(str(s), str(name), model_type=model_type)
        results.append(res)

    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file, index=False)

    # 统计
    intent_count = result_df["意图"].value_counts().to_dict()
    total = len(result_df)
    intent1 = intent_count.get(-1, 0)
    intent0 = intent_count.get(0, 0)
    print(f"\n处理完成: 共 {total} 条，意图=-1: {intent1} 条，意图=0: {intent0} 条，占比 {intent1/total:.2%}")

    return result_df

########################
# 测试入口
########################
if __name__ == '__main__':
    input_file = "sentences.xlsx"    # Excel 必须包含两列: sentence, ship_name
    output_file = "results_deepseek.xlsx"     # 输出表格
    model_type = "deepseek"              # 可选: qwen / deepseek / glm / wenxin

    df_result = process_excel(input_file, output_file, model_type)
    print("结果已保存到:", output_file)


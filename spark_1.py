# -*- coding: utf-8 -*-
import _thread as thread
import base64
import hashlib
import hmac
import json
import ssl
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime, time, sleep
import websocket
import pandas as pd

# ====== 请替换成你自己的讯飞开放平台参数 ======
APPID = "your id"
APIKey = "your API key"
APISecret = "your secret"
SPARK_URL = "wss://spark-api.xf-yun.com/v4.0/chat"
DOMAIN = "4.0Ultra"

# ====== WebSocket 参数类 ======
class Ws_Param:
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(self.APISecret.encode('utf-8'),
                                 signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        v = {"authorization": authorization, "date": date, "host": self.host}
        return self.Spark_url + '?' + urlencode(v)

def gen_params(appid, query, domain):
    return {
        "header": {"app_id": appid, "uid": "intent_checker"},
        "parameter": {"chat": {"domain": domain, "temperature": 0.0, "max_tokens": 100}},
        "payload": {"message": {"text": [
            {"role": "system", "content": """您是一个船舶意图分析器，请严格根据以下规则判断：
1. 找出句子中与输入船名最相似的船舶（考虑中文、拼音、英文大小写、数字差异）。
2. 如果该船舶明确表示要进入黄浦江（包括关键词如"黄浦江"、"张华浜"、"黄浦江内一些码头与泊位"等），返回 {"意图":-1}
3. 其他所有情况（包括其他目的地、无法判断、无关内容），返回 {"意图":0}

输出要求：
- 只输出 JSON 格式：{"意图":0或-1}
- 不要包含任何额外解释或文本"""
            },
            {"role": "user", "content": query}
        ]}}
    }

def extract_ship_intent_ws(sentence):
    result = {"意图": 0}
    answer_parts = []

    def on_message(ws, message):
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            print(f"请求错误: {code}, {data}")
            ws.close()
            return
        choices = data["payload"]["choices"]
        content = choices["text"][0]["content"]
        if content:
            answer_parts.append(content)
        if choices["status"] == 2:
            ws.close()

    def on_error(ws, error):
        print("### error:", error)

    def on_close(ws, close_status_code, close_msg):
        nonlocal result
        try:
            full_text = "".join(answer_parts).strip()
            if full_text.startswith("```") and full_text.endswith("```"):
                full_text = full_text[3:-3].strip()
            full_text = full_text.lstrip("json").strip()
            if full_text:
                result = json.loads(full_text)
        except Exception as e:
            print("解析最终 JSON 失败:", e)
            result = {"意图": 0}

    def on_open(ws):
        thread.start_new_thread(lambda w: w.send(json.dumps(gen_params(APPID, sentence, DOMAIN))), (ws,))

    ws_param = Ws_Param(APPID, APIKey, APISecret, SPARK_URL)
    ws_url = ws_param.create_url()

    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    return result

########################
# 批量处理 Excel
########################
def process_excel(input_file, output_file):
    df = pd.read_excel(input_file)
    if not {"sentence", "ship_name"}.issubset(df.columns):
        raise ValueError("Excel 必须包含列名 'sentence' 和 'ship_name'")

    results = []
    for sentence, ship_name in zip(df["sentence"], df["ship_name"]):
        start_time = datetime.now()
        start_ts = time()
        text = f"船名: {ship_name}\n句子: {sentence}"
        res = extract_ship_intent_ws(text)
        end_ts = time()
        end_time = datetime.now()
        elapsed = round(end_ts - start_ts, 3)
        results.append({
            "sentence": sentence,
            "ship_name": ship_name,
            "意图": res.get("意图", 0),
            "开始时间": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "结束时间": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "耗时秒": elapsed
        })
        # 防止请求过快
        sleep(0.5)

    result_df = pd.DataFrame(results)
    result_df.to_excel(output_file, index=False)

    intent_count = result_df["意图"].value_counts().to_dict()
    total = len(result_df)
    intent1 = intent_count.get(-1, 0)
    intent0 = intent_count.get(0, 0)
    print(f"\n处理完成: 共 {total} 条，意图=-1: {intent1} 条，意图=0: {intent0} 条，占比 {intent1/total:.2%}")

    return result_df

if __name__ == '__main__':
    input_file = "sentences.xlsx"
    output_file = "results_spark.xlsx"
    df_result = process_excel(input_file, output_file)
    print("结果已保存到:", output_file)


Ship-Shore Communication Intent Extraction using Chinese LLMs

This repository provides tools for extracting ship navigation intents from Chinese ship-shore communication text using various large language models (LLMs) developed in China. The system supports multiple models and enables batch processing of Excel files.

Features

LLM Ensemble (LLM_test): Integrates multiple LLMs including DeepSeek_V3, GLM_4, QWEN_3, ERINE_4.5 to improve extraction accuracy.

Single Model Support (spark_1): Uses Spark_4.0. 

After obtaining the API key, users can directly read sentence.xlsx and predict ship intents.

Batch Excel Processing: Reads input sentences from sentence.xlsx and outputs results in result.xlsx.

Model-Specific Results: Individual result files, e.g., result_qwen.xlsx, store extraction results using a single model for performance comparison.

Getting Started
Prerequisites

Python 3.9+

Required Python packages:

pip install openpyxl pandas requests


API keys for the LLM services you plan to use.

deepseek: https://platform.deepseek.com/api_keys
GLM_4: https://bigmodel.cn/usercenter/apikeys
QWEN_3: https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen
ERINE: https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application
spark: https://xinghuo.xfyun.cn

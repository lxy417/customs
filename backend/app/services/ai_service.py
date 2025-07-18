import os
import json
import httpx
from dotenv import load_dotenv
from app.config.settings import settings

# 加载环境变量
DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
DEEPSEEK_API_URL = settings.DEEPSEEK_API_URL

async def call_deepseek_api(search_value: str, export_countries: list[str], import_countries: list[str]):
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_URL:
        raise ValueError('DeepSeek API credentials not configured')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
    }

    system_prompt = f"""将用户输入的自然语言转换为海关数据查询条件，仅返回JSON格式，不包含任何解释文本，
    字段包括customs_code、export_country、import_country、start_date、end_date。
    customs_code:你需要根据商品名称转换为6位的海关代码
    时间用yyyy-mm-dd格式表示。
    export_country: 你只能从这几个中选择,其中"$$"是分隔符， $${'$$'.join(export_countries)}$$
    import_country: 你只能从这几个中选择"$$"是分隔符， $${'$$'.join(import_countries)}$$
    
    EXAMPLE INPUT: 查询越南出口未锻造锑的数据
    EXAMPLE JSON OUTPUT:
    {{
        "customs_code": "811010",
        "export_country": "Vietnam (VN)"
    }}
    """

    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt.strip()},
            {'role': 'user', 'content': search_value}
        ],
        'response_format': {'type': 'json_object'}
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return json.loads(content)
        except httpx.HTTPError as e:
            raise Exception(f'API request failed: {str(e)}')
        except (KeyError, IndexError) as e:
            raise Exception(f'Invalid API response format: {str(e)}')
        except json.JSONDecodeError as e:
            raise Exception(f'Failed to parse API response as JSON: {str(e)}')
        except Exception as e:
            raise Exception(f'Unexpected error: {str(e)}')
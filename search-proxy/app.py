import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 兼容Brave API路径，上层业务无需修改调用地址
@app.route('/res/v1/web/search', methods=['GET'])
def search_proxy():
    # 兼容Brave API的请求参数
    query = request.args.get('q', '')
    count = request.args.get('count', 10)
    offset = request.args.get('offset', 0)
    country = request.args.get('country', 'CN')
    search_lang = request.args.get('search_lang', 'zh')

    if not query:
        return jsonify({
            "type": "search",
            "web": {
                "results": [],
                "total": 0
            }
        }), 400

    # 调用字节跳动豆包搜索API
    ark_api_key = os.getenv('ARK_API_KEY', '')
    if not ark_api_key:
        return jsonify({"error": "ARK_API_KEY未配置"}), 500

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ark_api_key}"
    }

    payload = {
        "query": query,
        "count": int(count),
        "offset": int(offset),
        "country": country,
        "search_lang": search_lang,
        "freshness": "no_limit"
    }

    try:
        response = requests.post(
            "https://ark.cn-beijing.volces.com/api/v3/web/search",
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        doubao_result = response.json()

        # 转换为Brave API兼容的返回格式，上层业务完全无需修改
        brave_format_result = {
            "type": "search",
            "web": {
                "results": [],
                "total": len(doubao_result.get('data', []))
            },
            "query": {
                "original": query,
                "show_query": query
            }
        }

        for item in doubao_result.get('data', []):
            brave_format_result['web']['results'].append({
                "title": item.get('title', ''),
                "url": item.get('url', ''),
                "description": item.get('snippet', ''),
                "page_age": item.get('time', ''),
                "site": item.get('site_name', '')
            })

        return jsonify(brave_format_result)

    except Exception as e:
        return jsonify({
            "error": f"搜索请求失败: {str(e)}",
            "type": "search",
            "web": {"results": [], "total": 0}
        }), 500

# 健康检查接口
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "search-proxy", "provider": "doubao-search"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8300, debug=False)

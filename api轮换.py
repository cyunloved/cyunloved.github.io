from flask import Flask, request, jsonify
import requests
import threading
import random

app = Flask(__name__)

# 配置区 ========================================
API_KEYS = [
    "AIzaSyD6QgrS8TvR3ZQ0QRPxJoR8MYHlZXyR_9c",
    "AIzaSyBI8YCuZKimK8jSpwNvSuknAcfX2vqZbfk",  # 填入10+个Gemini API Key
    "AIzaSyAXSa5YIJed7zujpAGnlZU2j5YMGEJ4odU"
    "AIzaSyBmKZOs6zYxdlr2yAvxH6_gvERo_q68OPQ"
    "AIzaSyC6wjxf6FEz9Zh_PhVvpOJxcnWt2XaO6zU"
    "AIzaSyD9DvLsRrViwhQSzF-i9H_rFnOtFNzGlR8"
    "AIzaSyCwCwg0lGJfAwUke_J28n5j0AZdEOXLuGg"
    "AIzaSyBQl6P1WVlK1EVLVNWtCWJAukyaoHTuGTI"
    "AIzaSyB7JWMK9oYaIdrnAsV6iVSrI3UrQh9N5O8"
    "AIzaSyAAYsEH17IvzVaKawWiDlY0ZM-EcGiMkF0"
    "AIzaSyBjKfdldHSM33zrKn7gYj20Nbp-G1e_tSg"
    "AIzaSyAVpD6AhVTNfIVMXG_4n5dTrCyycENovL4"
    
]
USE_PROXY = True  # 是否启用代理IP轮换
PROXY_API = "http://api.proxy.com/get?format=json&num=5"  # 代理IP供应商接口
# ==============================================

# 全局变量
current_key_index = 0
request_counters = {key: 0 for key in API_KEYS}  # 统计各Key调用次数
lock = threading.Lock()

def get_proxy():
    """获取随机代理IP"""
    try:
        res = requests.get(PROXY_API).json()
        return {"http": f"http://{res['ip']}:{res['port']}"}
    except:
        return None

@app.route('/gemini-proxy', methods=['POST'])
def proxy():
    global current_key_index
    data = request.json
    headers = {'Content-Type': 'application/json'}

    # 轮换策略（可修改为随机模式）
    with lock:
        key = API_KEYS[current_key_index]
        current_key_index = (current_key_index + 1) % len(API_KEYS)
        request_counters[key] += 1

    # 构建请求参数
    proxies = get_proxy() if USE_PROXY else None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={key}"

    # 请求重试机制
    for _ in range(3):  # 最大重试3次
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers,
                proxies=proxies,
                timeout=10
            )
            
            # 处理限流错误
            if response.status_code == 429:
                print(f"⚠️ Key限流: {key[:8]}... 切换下一个")
                with lock:
                    current_key_index = (current_key_index + 1) % len(API_KEYS)
                continue
                
            return jsonify(response.json()), response.status_code
            
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")
    
    return jsonify({"error": "所有API请求失败"}), 500

@app.route('/stats')
def stats():
    """查看API调用统计"""
    return jsonify({
        "total_requests": sum(request_counters.values()),
        "key_usage": request_counters
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

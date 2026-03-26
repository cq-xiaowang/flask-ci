from flask import Flask, request, jsonify
import hmac
import hashlib
from builder import async_build
from config import CI_HOST, CI_PORT, WEBHOOK_SECRET, CI_DEBUG

app = Flask(__name__)

# 校验WebHook签名（安全）
def verify_signature(request):
    signature = request.headers.get("X-Hub-Signature256", "")
    if not signature:
        return False

    mac = hmac.new(WEBHOOK_SECRET.encode(), request.data, hashlib.sha256)
    return hmac.compare_digest(f"sha256={mac.hexdigest()}", signature)

# WebHook接收接口（Git仓库触发）
@app.route("/webhook", methods=["POST"])
def webhook():
    # 安全校验
    if not verify_signature(request):
        return jsonify({"status": "error", "msg": "签名校验失败"}), 403

    # 解析提交信息
    data = request.json
    project_name = "journey-blog-vue"  # 对应config中的项目名

    # 异步启动构建
    async_build(project_name)

    return jsonify({
        "status": "success",
        "msg": "构建任务已启动，后台执行中"
    })

# 健康检查
@app.route("/")
def index():
    return "CI系统运行中！"

if __name__ == "__main__":
    app.run(host=CI_HOST, port=CI_PORT)
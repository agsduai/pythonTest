# ===== 第409课：Web API 与接口测试-静态文件与简易前端 =====
# 知识点：
#   - Web 服务 = API + 静态资源（HTML/CSS/JS/图片）
#   - Content-Type 必须正确：text/html、text/css、application/javascript、image/png
#   - 路径穿越攻击：/../secret.txt 试图读目录外文件，必须拦截
#   - 安全做法：resolve 后校验 is_relative_to(root)，不靠字符串拼接
#   - 前端页面用 fetch 调 API 是最小可用的前后端分离
# 依赖：无（标准库）

import tempfile
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


class StaticHandler(BaseHTTPRequestHandler):
    root: Path = Path(".")

    def do_GET(self):
        url_path = self.path.split("?")[0]
        if url_path == "/":
            url_path = "/index.html"

        # ---- 安全：解析后必须在 root 内 ----
        candidate = (self.root / url_path.lstrip("/")).resolve()
        if not candidate.is_relative_to(self.root.resolve()):
            self._send_bytes(403, "text/plain; charset=utf-8", "403 禁止访问".encode())
            return
        if not candidate.is_file():
            self._send_bytes(404, "text/plain; charset=utf-8", "404 文件不存在".encode())
            return

        content_type = CONTENT_TYPES.get(candidate.suffix, "application/octet-stream")
        self._send_bytes(200, content_type, candidate.read_bytes())

    def _send_bytes(self, status, content_type, data: bytes):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>迷你前端</title></head>
<body>
  <h1>任务列表</h1>
  <ul id="list"></ul>
  <script src="/app.js"></script>
</body>
</html>
"""

JS = """// 调后端 API 并渲染列表
fetch('/api/tasks')
  .then(r => r.json())
  .then(data => {
    document.getElementById('list').innerHTML =
      data.map(t => `<li>${t.title}</li>`).join('');
  });
"""


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(HTML, encoding="utf-8")
        (root / "app.js").write_text(JS, encoding="utf-8")
        (root / "style.css").write_text("body { font-family: sans-serif; }", encoding="utf-8")
        (root.parent / "secret.txt").write_text("机密文件", encoding="utf-8")

        StaticHandler.root = root
        server = ThreadingHTTPServer(("127.0.0.1", 0), StaticHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = server.server_address[1]

        def fetch(path):
            conn = HTTPConnection("127.0.0.1", port, timeout=3)
            conn.request("GET", path)
            resp = conn.getresponse()
            body = resp.read()
            conn.close()
            return resp.status, resp.getheader("Content-Type"), body

        try:
            for path in ("/", "/app.js", "/style.css", "/missing.html"):
                status, ctype, body = fetch(path)
                preview = body[:60].decode("utf-8", errors="replace").replace("\n", " ")
                print(f"{path:16s} → {status} | {ctype} | {preview}")

            print("\n== 路径穿越测试 ==")
            status, ctype, body = fetch("/../secret.txt")
            print(f"/../secret.txt → {status} | {body.decode('utf-8', errors='replace')[:20]}")

            print("\n== 带查询串 ==")
            status, ctype, body = fetch("/app.js?v=2")
            print(f"/app.js?v=2 → {status} | {ctype}")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        (root.parent / "secret.txt").unlink(missing_ok=True)


main()

# ===== 练习题 =====
# 1. 增加 /api/tasks 接口，返回 JSON 数组，让页面能真正渲染数据。
# 2. 给静态服务加缓存头：Cache-Control: max-age=3600。
# 3. 验证 `/..%2fsecret.txt` 编码后的穿越是否也能拦住。
# 4. 思考：生产环境为什么通常用 Nginx 托管静态文件，而不是 Python 进程？

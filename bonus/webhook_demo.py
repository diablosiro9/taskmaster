from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()

        print("\n📩 WEBHOOK RECEIVED")
        try:
            print(json.dumps(json.loads(body), indent=2))
        except Exception:
            print(body)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return  # silence default logs

if __name__ == "__main__":
    print("🌐 Webhook demo listening on http://localhost:8080/webhook")
    server = HTTPServer(("localhost", 8080), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Webhook demo stopped cleanly")
        server.server_close()


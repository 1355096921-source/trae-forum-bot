import os
import re
import json
import shutil
from http.server import BaseHTTPRequestHandler, HTTPServer


ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
ENV_EXAMPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.example')
CONFIG_HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.html')

ENV_LINE_PATTERN = re.compile(r'^([A-Z_][A-Z0-9_]*)=(.*)$')


def read_env_file():
    if not os.path.exists(ENV_FILE):
        shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)

    result = {}
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if not line or line.strip().startswith('#'):
                continue
            match = ENV_LINE_PATTERN.match(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                result[key] = value
    return result


def write_env_file(new_values):
    with open(ENV_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = []
    for line in lines:
        stripped = line.rstrip('\n').rstrip('\r')
        match = ENV_LINE_PATTERN.match(stripped)
        if match:
            key = match.group(1)
            if key in new_values:
                newline = stripped[:match.start(2)] + new_values[key]
                if line.endswith('\r\n'):
                    newline += '\r\n'
                elif line.endswith('\n'):
                    newline += '\n'
                updated.append(newline)
            else:
                updated.append(line)
        else:
            updated.append(line)

    with open(ENV_FILE, 'w', encoding='utf-8') as f:
        f.writelines(updated)


class ConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._serve_html()
        elif self.path == '/api/config':
            self._serve_config()
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/api/config':
            self._update_config()
        else:
            self.send_error(404)

    def _serve_html(self):
        try:
            with open(CONFIG_HTML_FILE, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'config.html not found')

    def _serve_config(self):
        config = read_env_file()
        body = json.dumps(config, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _update_config(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            new_values = json.loads(body)
            write_env_file(new_values)
            response = json.dumps({'success': True}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except (json.JSONDecodeError, ValueError):
            self.send_error(400, 'Invalid JSON')

    def log_message(self, format, *args):
        pass


def main():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, ConfigHandler)
    print('配置页面已启动: http://localhost:8080')
    httpd.serve_forever()


if __name__ == '__main__':
    main()

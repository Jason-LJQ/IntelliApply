"""
Local web UI for browsing and editing job applications.

Runs in a background thread of the CLI, or standalone with:
    python -m intelliapply.web.server
"""

import re
import json
import threading
import webbrowser
from io import BytesIO
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from intelliapply.config.config import WEB_HOST, WEB_PORT
from intelliapply.config.prompt import ALL_FIELDS, REQUIRED_FIELDS
from intelliapply.utils.print_utils import print_

WEB_URL = f"http://{WEB_HOST}:{WEB_PORT}"
INDEX_HTML = Path(__file__).with_name("index.html")
JOB_PATH = re.compile(r'^/api/jobs/(\d+)(/mark)?$')
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class WebHandler(BaseHTTPRequestHandler):
    """JSON API over JobDatabase (available as self.server.job_db) plus the single-page UI."""

    def log_message(self, format, *args):
        pass  # Keep CLI output clean

    def do_GET(self):
        self._handle(self._get)

    def do_POST(self):
        self._handle(self._post)

    def do_PATCH(self):
        self._handle(self._patch)

    def do_DELETE(self):
        self._handle(self._delete)

    def _handle(self, route):
        try:
            # Requiring JSON forces a CORS preflight, so other websites cannot modify data
            if self.command != 'GET' and not self.headers.get('Content-Type', '').startswith('application/json'):
                return self._json({'error': 'Content-Type must be application/json'}, 415)
            route(urlparse(self.path))
        except ValueError as e:
            self._json({'error': str(e)}, 400)
        except Exception as e:
            self._json({'error': str(e)}, 500)

    def _send(self, status, body, content_type, headers=None):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data, status=200):
        self._send(status, json.dumps(data).encode(), 'application/json')

    def _read_json(self):
        length = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(length) or b'{}')

    def _get(self, url):
        job_db = self.server.job_db
        if url.path == '/':
            self._send(200, INDEX_HTML.read_bytes(), 'text/html; charset=utf-8')
        elif url.path == '/api/jobs':
            # Smart search (same as CLI) when q is given, otherwise all records
            q = parse_qs(url.query).get('q', [''])[0].strip()
            jobs = job_db.search_applications(search_term=q) if q else job_db.get_all_jobs()
            self._json({'fields': ALL_FIELDS, 'jobs': jobs})
        elif url.path == '/api/summary':
            self._json(job_db.get_summary())
        elif url.path == '/api/export':
            buffer = BytesIO()
            job_db.export_excel(buffer)
            filename = f"job_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            self._send(200, buffer.getvalue(), XLSX_TYPE,
                       {'Content-Disposition': f'attachment; filename="{filename}"'})
        else:
            self._json({'error': 'Not found'}, 404)

    def _post(self, url):
        job_db = self.server.job_db
        data = self._read_json()
        match = JOB_PATH.match(url.path)

        if url.path == '/api/jobs':
            record = {field: str(data.get(field) or '').strip() for field in ALL_FIELDS}
            missing = [field for field in REQUIRED_FIELDS if not record[field]]
            if missing:
                return self._json({'error': f"Required field(s) missing: {', '.join(missing)}"}, 400)
            if not data.get('force'):
                duplicate = job_db.check_duplicate_entry(new_data=record)
                if duplicate is not None:
                    return self._json({'error': 'This job entry already exists.', 'duplicate': duplicate}, 409)
            ids = job_db.append_data(data=[record])
            if not ids:
                return self._json({'error': 'Failed to add record.'}, 500)
            self._json(job_db.get_job(ids[0]), 201)
        elif match and match.group(2):
            job = job_db.set_status(int(match.group(1)), data.get('status'))
            if job is None:
                return self._json({'error': 'Record not found'}, 404)
            self._json(job)
        else:
            self._json({'error': 'Not found'}, 404)

    def _patch(self, url):
        match = JOB_PATH.match(url.path)
        if not match or match.group(2):
            return self._json({'error': 'Not found'}, 404)
        job = self.server.job_db.update_job(int(match.group(1)), self._read_json())
        if job is None:
            return self._json({'error': 'Record not found'}, 404)
        self._json(job)

    def _delete(self, url):
        match = JOB_PATH.match(url.path)
        if not match or match.group(2):
            return self._json({'error': 'Not found'}, 404)
        if not self.server.job_db.delete_job(int(match.group(1))):
            return self._json({'error': 'Record not found'}, 404)
        self._json({'ok': True})


def start_web_server(job_db, background=True):
    """
    Start the web UI server. Runs in a daemon thread if background is True, otherwise blocks.

    Returns:
        The server instance, or None if it failed to start (e.g. port in use by another instance)
    """
    try:
        server = ThreadingHTTPServer((WEB_HOST, WEB_PORT), WebHandler)
    except OSError as e:
        print_(f"Failed to start web UI at {WEB_URL} (another instance running?): {e}", "YELLOW")
        return None

    server.job_db = job_db
    print_(f"Web UI running at {WEB_URL}", "GREEN")
    if background:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    else:
        server.serve_forever()
    return server


def open_web_ui():
    """Open the web UI in the default browser."""
    webbrowser.open(WEB_URL)
    print_(f"Web UI opened at {WEB_URL}", "GREEN")


if __name__ == "__main__":
    from intelliapply.utils.db_utils import JobDatabase

    try:
        start_web_server(JobDatabase(), background=False)
    except KeyboardInterrupt:
        print_("\nExiting ...", "RED")

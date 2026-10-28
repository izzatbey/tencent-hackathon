#!/usr/bin/env python3
"""HTTP API tipis SecuritySahabat (stdlib saja).

Membungkus process_query() dan hanya mengeluarkan field yang aman ke browser
(kontrak: docs/architecture.md §4).

    python backend/api/server.py                     # 127.0.0.1:8787
    python backend/api/server.py --static frontend/dist   # sekalian melayani UI hasil build
    python backend/api/server.py --demo              # + POST /api/demo/clock
    python backend/api/server.py --replay Q-0091a2d7fa37  # baca ulang catatan audit
    PORT=8080 python backend/api/server.py --static frontend/dist  # bind 0.0.0.0 (WorkBuddy Sites)

Endpoint:
    POST /api/ask       {"question": "...", "user": null, "role": null}
    GET  /api/personas  daftar persona demo (nama + role saja)
    GET  /api/health
    Pra-CAB (change request): lihat api/cab_api.py

Setiap pertanyaan dan setiap event Pra-CAB dicatat ke satu audit log JSONL
berantai hash (env SECURITY_SAHABAT_AUDIT_LOG, default backend/logs/audit.jsonl).
Log hanya memuat teks yang sudah disamarkan, tidak pernah teks mentahnya.
"""

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ask_bridge  # noqa: E402
import cab_api  # noqa: E402
import injection_guard as guard  # noqa: E402
import permissions as perm  # noqa: E402
import search_kb  # noqa: E402
from audit_chain import AuditChain  # noqa: E402
from policy_register import PolicyError  # noqa: E402  (induk CabError)

MAX_BODY = 64 * 1024
MAX_DRAIN = 1024 * 1024
MAX_QUESTION = 2000
MAX_NAME = 80
SOCKET_TIMEOUT = 15
DEFAULT_LOG = BACKEND / "logs" / "audit.jsonl"

# SKILL.md §Eskalasi, baris "Lainnya / tidak ada owner". Sengaja tetap: jawaban
# "tidak tahu" untuk topik restricted dan topik fiktif harus identik.
FALLBACK_SME = "Andini Pratama (IT Admin)"

NO_MATCH_ANSWER = ("Saya tidak tahu. Hal ini belum tercakup di knowledge base, "
                   "dan saya tidak akan menebak.")
INJECTION_ANSWER = ("Pertanyaan ini berisi perintah yang ditujukan langsung ke sistem, "
                    "jadi tidak diproses. Ulangi dengan bahasa biasa, misalnya "
                    "\"Apakah X diperbolehkan?\".")

CITATION_FIELDS = ("doc_id", "title", "section", "quote", "owner", "effective_date",
                   "status", "risk_level")


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


# --------------------------------------------------------------------------
# request -> process_query -> response
# --------------------------------------------------------------------------
def parse_json(body, content_type):
    if "application/json" not in (content_type or "").lower():
        raise ApiError(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "unsupported_media_type",
                       "Kirim body sebagai application/json.")
    try:
        data = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid_json", "Body bukan JSON yang valid.")
    if not isinstance(data, dict):
        raise ApiError(HTTPStatus.BAD_REQUEST, "invalid_json", "Body harus berupa objek JSON.")
    return data


def parse_request(body, content_type):
    data = parse_json(body, content_type)
    question = data.get("question")
    # Karakter tak terlihat saja (zero-width, BOM) dihitung kosong.
    if not isinstance(question, str) or not guard.normalize(question).strip():
        raise ApiError(HTTPStatus.BAD_REQUEST, "question_required", "Pertanyaan wajib diisi.")
    if len(question) > MAX_QUESTION:
        raise ApiError(HTTPStatus.BAD_REQUEST, "question_too_long",
                       "Pertanyaan maksimal %d karakter." % MAX_QUESTION)

    fields = {}
    for key in ("user", "role"):
        value = data.get(key)
        if value is not None and (not isinstance(value, str) or len(value) > MAX_NAME):
            raise ApiError(HTTPStatus.BAD_REQUEST, "invalid_%s" % key,
                           "Field %s harus teks maksimal %d karakter." % (key, MAX_NAME))
        fields[key] = (value.strip() or None) if isinstance(value, str) else None
    # role hanya divalidasi demi kompatibilitas klien; hak akses diturunkan dari user.
    return question.strip(), fields["user"]


def public_identity(result):
    identity = result.get("identity") or {}
    perms = result.get("permissions") or {}
    if not identity.get("authenticated"):
        return {"user": None, "role": None}
    return {"user": perms.get("user"), "role": perms.get("role")}


def to_response(result, q_id):
    """Hasil internal -> DTO publik. Field di luar daftar ini tidak pernah keluar."""
    base = {"q_id": q_id, "citations": [], "flags": [], "escalation": None}

    if result["status"] == "INJECTION_DETECTED":
        return dict(base, status="INJECTION_DETECTED", rc=4, answer=INJECTION_ANSWER,
                    question_masked=None, identity={"user": None, "role": None},
                    pii_masked="")

    common = dict(base, question_masked=result.get("masked_query"),
                  identity=public_identity(result), pii_masked=result.get("pii_masked") or "")

    if result["status"] == "NO_MATCH":
        return dict(common, status="NO_MATCH", rc=3, answer=NO_MATCH_ANSWER,
                    escalation=FALLBACK_SME)

    citations = [{k: hit.get(k) for k in CITATION_FIELDS} for hit in result["hits"]]
    flags = [{"type": f["type"], "doc": f["doc"], "detail": f["detail"]}
             for f in result.get("flags", [])]
    owner = next((c["owner"] for c in citations if c.get("owner")), FALLBACK_SME)
    # answer null kecuali jembatan (merge_bridge) punya klarifikasi atau verdict
    # dari aturan; tanpa LLM, API tidak menyimpulkan boleh/tidak dari bukti bebas.
    return dict(common, status="OK", rc=0, answer=None, citations=citations,
                flags=flags, escalation=owner)


def merge_bridge(response, bridge):
    """Tempel klarifikasi / verdict aturan dari ask_bridge ke DTO yang sama.
    Tidak ada field baru: hanya answer, flags, dan citations yang bertambah."""
    if not bridge["answer_parts"]:
        return response
    answer = " ".join(bridge["answer_parts"])
    if response["status"] == "NO_MATCH":
        answer += " Untuk bagian lain dari pertanyaan ini: " + NO_MATCH_ANSWER
    have = {(c["doc_id"], c["quote"]) for c in response["citations"]}
    extra = [c for c in bridge["citations"] if (c["doc_id"], c["quote"]) not in have]
    return dict(response, answer=answer, flags=response["flags"] + bridge["flags"],
                citations=response["citations"] + extra)


# --------------------------------------------------------------------------
# audit log (S6): satu rantai hash untuk tanya-jawab dan Pra-CAB
# --------------------------------------------------------------------------
def audit_path():
    return Path(os.environ.get("SECURITY_SAHABAT_AUDIT_LOG") or DEFAULT_LOG)


def audit(result, response, bridge=None):
    perms = result.get("permissions") or {}
    bridge = bridge or {"approval_state": "n/a", "summary": None}
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "q_id": response["q_id"],
        "stage": "answer",
        "actor": "api",
        "user": response["identity"]["user"],
        "zones_searched": perms.get("allowed_zones", []),
        "status": response["status"],
        "question_masked": response["question_masked"],
        "pii_masked": response["pii_masked"],
        "citations": [c["doc_id"] for c in response["citations"]],
        "flags": [f["type"] for f in response["flags"]],
        "answer_sha256": hashlib.sha256((response["answer"] or "").encode("utf-8")).hexdigest(),
        # pending/blocked = ada permintaan aksi yang TIDAK dijalankan (S5)
        "approval_state": bridge["approval_state"],
        "bridge": bridge["summary"],
    }
    write_log(record)


def write_log(record):
    # Galat menulis sengaja tidak ditangkap: ask() gagal, jawaban tidak dikirim.
    AuditChain.for_path(audit_path()).append(record)


def ask(question, user=None, kb_root=None):
    """Identitas hanya dari `user` yang terdaftar persis di permissions.csv.

    Klaim di teks pertanyaan ("Saya Andini, IT Admin") dan field role tidak
    dipakai: otorisasi ditetapkan pemanggil, bukan isi prompt (OWASP LLM01).
    Bila audit log gagal ditulis, jawaban tidak dikirim (fail closed).
    """
    q_id = "Q-" + uuid.uuid4().hex[:12]
    user = user if user in {p["user"] for p in personas()} else None
    try:
        result = search_kb.process_query(question, kb_root=kb_root, user=user,
                                         identity_from_text=False)
    except Exception:
        write_log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "q_id": q_id, "stage": "answer", "actor": "api", "user": user,
                   "status": "ERROR"})
        raise
    response = to_response(result, q_id)
    bridge = None
    if result["status"] != "INJECTION_DETECTED":
        # klarifikasi & verdict aturan dari register yang sama dengan Pra-CAB,
        # dibaca dari pertanyaan yang sudah disamarkan PII-nya
        policies = cab_api.store_for(audit_path()).policies
        with policies.lock:
            rules, submitted = policies.active_rules(), dict(policies.sources)
        bridge = ask_bridge.analyze(result.get("masked_query") or "", user=user, rules=rules,
                                    submitted=submitted, root=kb_root, now=cab_api.CLOCK.now())
        response = merge_bridge(response, bridge)
    audit(result, response, bridge)
    return response


def personas():
    return [{"user": row["user"], "role": row["role"]} for row in perm.load_permissions_rows()]


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------
STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript",
                ".css": "text/css", ".svg": "image/svg+xml", ".woff2": "font/woff2",
                ".woff": "font/woff", ".png": "image/png", ".ico": "image/x-icon",
                ".json": "application/json", ".webmanifest": "application/manifest+json"}
CSP = ("default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")


class Handler(BaseHTTPRequestHandler):
    server_version = "SecuritySahabat"
    sys_version = ""
    static_root = None
    kb_root = None
    demo = False

    def log_message(self, fmt, *args):  # tanpa query string / body di log akses
        # Koneksi keep-alive yang diam lalu kena timeout belum punya request line,
        # jadi command/path belum ada; tidak ada yang perlu dicatat.
        if not getattr(self, "command", None):
            return
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?")[0]))

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, err, allow=None):
        self.send_response(err.status)
        body = json.dumps({"error": {"code": err.code, "message": err.message}}).encode("utf-8")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if allow:
            self.send_header("Allow", allow)
        self.end_headers()
        self.wfile.write(body)

    def route(self):
        return self.path.split("?", 1)[0]

    def query(self):
        return self.path.split("?", 1)[1] if "?" in self.path else ""

    def read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0:
            raise ApiError(400, "invalid_length", "Content-Length tidak valid.")
        if length > MAX_BODY:
            # Body yang belum terbaca membuat socket di-reset (terutama di Windows),
            # sehingga klien menerima "connection reset" alih-alih 413. Buang dulu
            # sampai batas wajar; di atas itu koneksi memang diputus.
            remaining = min(length, MAX_DRAIN)
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 64 * 1024))
                if not chunk:
                    break
                remaining -= len(chunk)
            self.close_connection = True
            raise ApiError(413, "too_large", "Body terlalu besar.")
        try:
            return self.rfile.read(length)
        except TimeoutError:  # Content-Length lebih besar dari body yang benar-benar dikirim
            self.close_connection = True
            raise ApiError(408, "timeout", "Body tidak lengkap.")

    def run(self, label, fn):
        try:
            self.send_json(200, fn())
        except (ApiError, PolicyError) as err:
            self.send_error_json(err)
        except Exception as exc:  # jangan bocorkan stack trace atau isi permintaan
            sys.stderr.write("%s gagal: %s\n" % (label, type(exc).__name__))
            self.send_error_json(ApiError(500, "internal", "Terjadi kesalahan di server."))

    def do_POST(self):
        path = self.route()
        if path in ("/api/personas", "/api/health", "/api/audit/verify"):
            return self.send_error_json(ApiError(405, "method_not_allowed", "Pakai GET."), "GET")
        if path != "/api/ask" and not cab_api.handles(path):
            return self.send_error_json(ApiError(404, "not_found", "Tidak ditemukan."))
        try:
            body = self.read_body()
        except ApiError as err:
            return self.send_error_json(err)
        content_type = self.headers.get("Content-Type")
        if path == "/api/ask":
            def answer():
                question, user = parse_request(body, content_type)
                return ask(question, user=user, kb_root=self.kb_root)
            return self.run("ask", answer)
        self.run("cab", lambda: cab_api.handle_post(path, parse_json(body, content_type),
                                                    audit_path(), demo=self.demo))

    def do_GET(self):
        path = self.route()
        if path == "/api/ask":
            return self.send_error_json(ApiError(405, "method_not_allowed", "Pakai POST."), "POST")
        if path == "/api/personas":
            return self.send_json(200, {"personas": personas()})
        if path == "/api/health":
            return self.send_json(200, {"ok": True})
        if path in ("/api/intake", "/api/demo/clock"):
            return self.send_error_json(ApiError(405, "method_not_allowed", "Pakai POST."), "POST")
        if cab_api.handles(path):
            return self.run("cab", lambda: cab_api.handle_get(path, self.query(), audit_path()))
        if path.startswith("/api/") or not self.static_root:
            return self.send_error_json(ApiError(404, "not_found", "Tidak ditemukan."))
        self.serve_static(path)

    def serve_static(self, path):
        root = Path(self.static_root).resolve()
        target = (root / path.lstrip("/")).resolve()
        if root not in target.parents and target != root:
            return self.send_error_json(ApiError(404, "not_found", "Tidak ditemukan."))
        if not target.is_file():
            target = root / "index.html"  # SPA fallback
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", STATIC_TYPES.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)


def make_server(host="127.0.0.1", port=8787, static_root=None, kb_root=None,
                timeout=SOCKET_TIMEOUT, demo=False):
    # timeout: koneksi yang diam (slowloris, body terpotong) tidak menahan thread selamanya.
    handler = type("BoundHandler", (Handler,), {"static_root": static_root, "kb_root": kb_root,
                                                "timeout": timeout, "demo": demo})
    return ThreadingHTTPServer((host, port), handler)


def replay(q_id):
    """Semua baris audit log untuk satu q_id (tes #17: rantai bisa direkonstruksi)."""
    return [r for r in AuditChain.for_path(audit_path()).records() if r.get("q_id") == q_id]


def main():
    ap = argparse.ArgumentParser(description="HTTP API SecuritySahabat.")
    # WorkBuddy Sites menyuntikkan PORT dan butuh bind 0.0.0.0; lokal tetap 127.0.0.1.
    ap.add_argument("--host", default=os.environ.get("HOST")
                    or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT") or 8787))
    ap.add_argument("--static", help="Folder UI hasil build (mis. frontend/dist)")
    ap.add_argument("--demo", action="store_true",
                    help="Aktifkan POST /api/demo/clock (memajukan jam untuk demo rapat CAB)")
    ap.add_argument("--replay", metavar="Q_ID", help="Cetak catatan audit untuk q_id ini lalu keluar")
    args = ap.parse_args()
    if args.replay:
        records = replay(args.replay)
        for record in records:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0 if records else 1
    server = make_server(args.host, args.port, args.static, demo=args.demo)
    print("SecuritySahabat API di http://%s:%d" % server.server_address[:2], flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

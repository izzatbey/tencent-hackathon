#!/usr/bin/env python3
"""Jembatan tanya-jawab -> Pra-CAB: klarifikasi dan pratinjau aturan, tanpa LLM.

Dipanggil `/api/ask` setelah process_query(). Semua keluaran ditentukan aturan
dan data KB (direktori, CMDB, policy register), bukan model bahasa:

  klarifikasi  nama yang dimiliki lebih dari satu staf ("Pak Budi"), jadwal
               tanpa zona waktu ("Jumat siang"), aset yang tidak jelas
               ("server yang itu di gudang Makassar");
  aksi         kalimat perintah ("tolong bukakan port 22 sekarang") tidak
               pernah dijalankan; dicatat approval_state pending/blocked;
  pratinjau    bila pesan menyebut aset + jenis perubahan, precheck Pra-CAB
               dijalankan (tanpa menyimpan CR) dan verdict aturannya dikutip:
               "tidak boleh" hanya bila ada aturan BLOCK.

Non-interference (ADR 0002) tetap: jembatan hanya membaca direktori, CMDB, dan
register, yang sama untuk semua persona; dokumen restricted tidak disentuh.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cab_rules  # noqa: E402
import kb_facts  # noqa: E402
import policy_register  # noqa: E402

DAYS = {"senin": 0, "selasa": 1, "rabu": 2, "kamis": 3, "jumat": 4, "jum'at": 4, "sabtu": 5,
        "minggu": 6, "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4,
        "saturday": 5, "sunday": 6}
DAY_RE = re.compile(r"\b(%s)\b(?:\s+(pagi|siang|sore|malam|malem|morning|afternoon|evening|night))?"
                    % "|".join(re.escape(d) for d in DAYS), re.I)
CLOCK_RE = re.compile(r"\b(?:jam|pukul|at)\s+\d{1,2}(?:[.:]\d{2})?\b", re.I)
ZONE_RE = re.compile(r"\b(WIB|WITA|WIT)\b")
SCHEDULE_CUE = re.compile(r"\b(jadwal\w*|schedule\w*|meeting|rapat|book\w*|bisakah|bisa|kapan|when)\b", re.I)
SENTENCE_RE = re.compile(r"[^.?!\n]+[.?!]?")

# perintah: kata sopan, kata kerja -kan di awal kalimat, atau bentuk lisan -in yang umum
IMPERATIVE = re.compile(r"\b(tolong|mohon|minta|please|pls|tlg|jadwalin|kirimin|bukain|kasihin|pasangin|"
                        r"terusin|matiin|hapusin)\b|^\s*(?:\w+\s+)?\w+kan\b", re.I)
QUESTION_CUE = re.compile(r"\?|\b(boleh\w*|apakah|bisakah|gimana|bagaimana|perlu|is it|can i|may i|"
                          r"should i|what|kenapa|why|siapa|who)\b", re.I)
ACTION_VERBS = re.compile(r"\b(buka\w*|open|tutup\w*|close|install\w*|pasang\w*|beri\w*|kasih\w*|grant|"
                          r"upgrade\w*|update\w*|ubah\w*|ganti\w*|change|hapus\w*|delete|matikan|"
                          r"nonaktif\w*|disable|restart|reboot|kirim\w*|send|jadwal\w*|schedule|"
                          r"expose|ekspos\w*|forward|teruskan|terusin)\b", re.I)
# "terus" saja berarti "lalu", bukan "meneruskan"
VERB_LABELS = (("kirim", "mengirim"), ("send", "mengirim"), ("forward", "meneruskan"), ("teruskan", "meneruskan"),
               ("terusin", "meneruskan"),
               ("jadwal", "menjadwalkan"), ("schedule", "menjadwalkan"))

VAGUE_RE = re.compile(r"\b(server|mesin|aset|asset|perangkat|firewall|router|switch|aplikasi|sistem|database|db)"
                      r"\s+(yang\s+itu|yang\s+tadi|itu|tersebut|tadi)\b", re.I)
TYPE_WORDS = {"firewall": "Firewall", "switch": "Switch", "database": "Database", "db": "Database",
              "cluster": "Cluster", "kubernetes": "Cluster", "k8s": "Cluster"}
SITES = {"jakarta": "Jakarta", "jkt": "Jakarta", "hq": "Jakarta", "makassar": "Makassar", "mks": "Makassar",
         "jayapura": "Jayapura"}
# kata Indonesia tanpa peduli kapital; "I" Inggris harus kapital supaya "i" lain tidak terbaca
FIRST_PERSON = re.compile(r"\b([Ss]aya|[Aa]ku|[Gg]ue|I|[Mm]e|[Mm]y)\b")
HONORIFIC = r"(?:Pak|Bu|Bapak|Ibu|Mas|Mbak|Mr\.?|Ms\.?|Mrs\.?)"

# urutan penting: yang lebih spesifik dulu
CHANGE_KINDS = (
    ("firmware_upgrade", re.compile(r"\bfirmware\b", re.I)),
    ("firewall_rule", re.compile(r"\b(port|nat|port[- ]forward\w*|rule firewall|firewall rule|expose|ekspos\w*)\b", re.I)),
    ("access_grant", re.compile(r"\b(akses|access)\b", re.I)),
    ("software_install", re.compile(r"\b(install\w*|pasang\w*)\b", re.I)),
    ("backup_change", re.compile(r"\bbackup\b", re.I)),
    ("config_change", re.compile(r"\b(remote|disable|matikan|nonaktif\w*|restart|reboot|ubah\w*|change|"
                                 r"konfigurasi|config\w*)\b", re.I)),
)
INTERNET = re.compile(r"\b(dari|from|ke|to|via)\s+(the\s+)?internet\b|\binternet\b.*\b(expose|ekspos\w*|nat|buka\w*|open)\b|"
                      r"\b(expose|ekspos\w*|nat|buka\w*|open)\b.*\binternet\b", re.I)
PORT_RE = re.compile(r"\bport\s*(\d{1,5})\b", re.I)
PREVIEW_SKIP = {"ASSETS", "FIELDS", "ACCESS", "RISK", "INJECTION"}


def _sentences(text):
    return [s.strip() for s in SENTENCE_RE.findall(text or "") if s.strip()]


def _cite(c):
    return {"doc_id": c.get("doc_id"), "title": c.get("title"), "section": c.get("section"),
            "quote": c.get("quote"), "owner": c.get("owner"), "effective_date": c.get("effective_date"),
            "status": None, "risk_level": None}


class Bridge:
    def __init__(self, rules, submitted=None, root=None):
        self.root = kb_facts.kb_root(root)
        self.rules = rules
        self.submitted = submitted or {}
        self.cmdb = kb_facts.load_cmdb(self.root)
        self.directory = kb_facts.load_directory(self.root)

    # ---- klarifikasi ----------------------------------------------------------
    def ambiguous_people(self, text):
        """Nama depan yang dimiliki >1 staf dan tidak diikuti nama belakang yang jelas."""
        by_first = {}
        for p in self.directory:
            by_first.setdefault(p["name"].split()[0], []).append(p)
        out = []
        for first, people in sorted(by_first.items()):
            if len(people) < 2:
                continue
            for m in re.finditer(r"\b(?:%s\s+)?%s\b(\s+[A-Z][a-z]+)?" % (HONORIFIC, re.escape(first)), text):
                last = (m.group(1) or "").strip()
                if not any(p["name"].split()[-1] == last for p in people):
                    out.append({"term": m.group(0).strip(), "candidates": people})
                    break
        return out

    def vague_assets(self, text):
        sentence = next((s for s in _sentences(text) if VAGUE_RE.search(s)), None)
        if sentence is None:
            return None
        m = VAGUE_RE.search(sentence)
        # site hanya dari kalimat yang sama: "replikasi ke Jakarta" di kalimat lain bukan petunjuk
        sites = sorted({SITES[w.lower()] for w in re.findall(r"\b\w+\b", sentence) if w.lower() in SITES})
        candidates = [a for a in self.cmdb.values() if not sites or a["site"] in sites]
        return {"term": m.group(0), "sites": sites, "candidates": sorted(candidates, key=lambda a: a["asset_id"])}

    def resolve_assets(self, text):
        """asset_id yang disebut persis + (jenis + site) yang hanya punya satu kandidat.
        Mengembalikan (aset pasti, kelompok ambigu)."""
        found = [a for a in sorted(self.cmdb) if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(a), text, re.I)]
        words = [w.lower() for w in re.findall(r"[\w-]+", text)]
        ambiguous = []
        for i, w in enumerate(words):
            if w not in TYPE_WORDS:
                continue
            near = {SITES[x] for x in words[max(0, i - 3):i + 4] if x in SITES}
            for site in sorted(near):
                hits = [a for a in self.cmdb.values() if a["type"] == TYPE_WORDS[w] and a["site"] == site]
                if len(hits) == 1 and hits[0]["asset_id"] not in found:
                    found.append(hits[0]["asset_id"])
                elif len(hits) > 1 and not any(h["asset_id"] in found for h in hits):
                    ambiguous.append({"term": "%s %s" % (w, site),
                                      "candidates": sorted(hits, key=lambda a: a["asset_id"])})
        return found, ambiguous

    def schedule_phrases(self, text):
        """Frasa hari/jam tanpa zona waktu di kalimat yang memang meminta jadwal."""
        out = []
        for sentence in _sentences(text):
            if ZONE_RE.search(sentence) or not SCHEDULE_CUE.search(sentence):
                continue
            m = DAY_RE.search(sentence) or CLOCK_RE.search(sentence)
            if m:
                day = DAYS.get(m.group(1).lower()) if m.re is DAY_RE else None
                out.append({"term": m.group(0), "weekday": day})
        return out

    def prayer_rules(self, day):
        return [r for r in self.rules if r.get("check_id") == "FRIDAY-PRAYER"
                and policy_register.in_force(r, day)]

    # ---- aksi & perubahan -------------------------------------------------------
    def action_sentences(self, text):
        return [s for s in _sentences(text)
                if ACTION_VERBS.search(s) and IMPERATIVE.search(s) and not QUESTION_CUE.search(s)]

    def change_signals(self, text):
        kind = next((k for k, pattern in CHANGE_KINDS if pattern.search(text)), None)
        ports = sorted({int(p) for p in PORT_RE.findall(text) if 0 < int(p) < 65536})
        if re.search(r"\bssh\b", text, re.I):
            ports = sorted(set(ports) | {22})
        exposure = "internet" if INTERNET.search(text) else "none"
        if kind is None and (exposure == "internet" or ports):
            kind = "firewall_rule"  # "bukakan SSH dari internet" = perubahan rule, walau tanpa kata "port"
        return {"change_kind": kind, "exposure": exposure, "ports": ports}

    # ---- utama ------------------------------------------------------------------
    def analyze(self, text, user=None, now=None):
        """Mengembalikan dict {answer_parts, flags, citations, approval_state, summary}."""
        parts, flags, citations = [], [], []
        summary = {"clarify": [], "action": False, "preview": None}
        day = (now or cab_rules.datetime.now(kb_facts.tz("WIB"))).astimezone(kb_facts.tz("WIB")).date().isoformat()

        people = self.ambiguous_people(text)
        for amb in people:
            options = " atau ".join("%s (%s, %s, %s)" % (p["name"], p["role"], p["office"], p["timezone"])
                                    for p in amb["candidates"])
            parts.append("%s yang mana: %s?" % (amb["term"], options))
            flags.append({"type": "CLARIFY", "doc": "directory", "detail": "Nama '%s' dimiliki %d staf: %s."
                          % (amb["term"], len(amb["candidates"]), options)})
            summary["clarify"].append("person")

        assets, ambiguous_assets = self.resolve_assets(text)
        vague = self.vague_assets(text) if not assets else None
        groups = ambiguous_assets + ([vague] if vague else [])
        for group in groups:
            options = ", ".join("%s (%s, %s)" % (a["asset_id"], a["name"], a["site"]) for a in group["candidates"])
            where = " di %s" % ", ".join(group.get("sites") or []) if group.get("sites") else ""
            parts.append("'%s' yang mana? Kandidat%s dari CMDB: %s. Sebutkan asset_id-nya; saya tidak menebak."
                         % (group["term"], where, options))
            flags.append({"type": "CLARIFY", "doc": "CMDB", "detail": "Aset tidak jelas ('%s'): %s." % (group["term"], options)})
            summary["clarify"].append("asset")

        schedules = self.schedule_phrases(text)
        if schedules:
            parties = ["%s (%s)" % (p["name"], p["timezone"]) for amb in people for p in amb["candidates"]]
            parties += ["%s (%s, %s)" % (a, self.cmdb[a]["site"], kb_facts.SITE_TZ.get(self.cmdb[a]["site"], "WIB"))
                        for a in assets]
            for s in schedules:
                text_part = "'%s' dalam zona apa: WIB, WITA, atau WIT?" % s["term"]
                if parties:
                    text_part += " Pihak terkait: %s." % ", ".join(parties)
                prayers = self.prayer_rules(day) if s["weekday"] == 4 else []
                if prayers:
                    windows = []
                    for rule in prayers:
                        cond = rule["condition"]["schedule_overlaps"]
                        site = rule["subject"].get("site")
                        windows.append("%s %s-%s %s" % (site, cond["from"], cond["to"],
                                                        kb_facts.SITE_TZ.get(site, "WIB")))
                        citations += [_cite(c) for c in policy_register.verify_sources(
                            rule, kb_facts._documents(self.root), self.cmdb, self.root, self.submitted)]
                    text_part += (" Hari Jumat ada salat Jumat (%s); usulan: mulai setelah jam itu, mis. %s."
                                  % ("; ".join(windows),
                                     " / ".join("%s %s" % (w.split()[1].split("-")[1], w.split()[2]) for w in windows)))
                parts.append(text_part)
                flags.append({"type": "CLARIFY", "doc": "jadwal", "detail": "Jadwal '%s' tanpa zona waktu." % s["term"]})
                summary["clarify"].append("timezone")

        actions = self.action_sentences(text)
        if actions:
            verbs = sorted({label for s in actions for key, label in VERB_LABELS if key in s.lower()})
            parts.append("Pesan ini berisi permintaan aksi%s. SecuritySahabat tidak menjalankan aksi dari chat: "
                         "tidak ada yang dikirim, dijadwalkan, atau diubah."
                         % (" (%s)" % ", ".join(verbs) if verbs else ""))
            flags.append({"type": "ACTION_REQUEST", "doc": "Pra-CAB",
                          "detail": "Permintaan aksi dicatat dan tidak dijalankan; menunggu persetujuan manusia."})
            summary["action"] = True

        signals = self.change_signals(text)
        approval_state = "pending" if actions else "n/a"
        if assets and signals["change_kind"]:
            preview = self.preview(assets, signals, user, text, now)
            summary["preview"] = {"outcome": preview["outcome"], "risk": preview["risk"]["level"],
                                  "rules": sorted({p["id"] for p in preview.get("policies", []) if p["triggered"]})}
            part, cites, blocked = self.verdict(preview)
            parts.append(part)
            citations += cites
            rules = ", ".join(summary["preview"]["rules"]) or "-"
            flags.append({"type": "POLICY_BLOCK" if blocked else "POLICY_PREVIEW", "doc": "policy register",
                          "detail": ("Diblokir aturan %s." % rules) if blocked else
                          ("Pratinjau: risiko %s; aturan terpicu: %s." % (preview["risk"]["level"], rules))})
            if actions:
                approval_state = "blocked" if blocked else "pending"

        seen, unique = set(), []
        for c in citations:
            key = (c["doc_id"], c["quote"])
            if key not in seen:
                seen.add(key)
                unique.append(c)
        summary["clarify"] = sorted(set(summary["clarify"]))
        return {"answer_parts": parts, "flags": flags, "citations": unique,
                "approval_state": approval_state, "summary": summary}

    def preview(self, assets, signals, user, text, now):
        kind = signals["change_kind"]
        cr = {"type": "access" if kind == "access_grant" else "change", "assets": assets, "change_kind": kind,
              "exposure": signals["exposure"], "ports": signals["ports"],
              "requester": {"user": user} if user else {}}
        if kind == "access_grant" and user and FIRST_PERSON.search(text):
            cr["access"] = {"grantee": user}
        moment = now or cab_rules.datetime.now(kb_facts.tz("WIB"))
        return cab_rules.precheck(cr, moment, root=self.root, rules=self.rules, submitted=self.submitted)

    def verdict(self, pre):
        """Teks verdict dari hasil precheck. 'Tidak boleh' hanya bila ada BLOCK."""
        relevant = [c for c in pre["checks"] if c["id"] not in PREVIEW_SKIP]
        blocks = [c for c in relevant if c["status"] == "BLOCK"]
        cites = [_cite(x) for c in (blocks or [c for c in relevant if c["status"] in ("WARN", "FAIL")])
                 for x in c["citations"]]
        tag = lambda c: c.get("rule_id") or c["id"]  # noqa: E731
        if blocks:
            text = "Menurut aturan perusahaan: tidak boleh. %s" % " ".join(
                "%s [%s]" % (c["detail"], tag(c)) for c in blocks)
        else:
            approvers = ", ".join("%s (%s)" % (s["label"], s["assignee"]) for s in pre["approvals"])
            warns = [c for c in relevant if c["status"] in ("WARN", "FAIL")]
            text = ("Menurut aturan perusahaan: boleh diajukan sebagai change request, risiko %s, "
                    "persetujuan: %s." % (pre["risk"]["level"], approvers or "-"))
            if warns:
                text += " Perhatian: %s" % " ".join("%s [%s]" % (c["detail"], tag(c)) for c in warns)
        text += (" Ini pratinjau dari aturan, tidak ada yang dijalankan; ajukan lewat Pra-CAB untuk "
                 "pemeriksaan lengkap (jadwal, rollback, lead time CAB).")
        return text, cites, bool(blocks)


def analyze(text, user=None, rules=None, submitted=None, root=None, now=None):
    rules = rules if rules is not None else policy_register.load_seed(root)
    return Bridge(rules, submitted, root).analyze(text, user=user, now=now)

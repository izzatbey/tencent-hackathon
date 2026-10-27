# Pra-CAB — kontrak API untuk frontend

Pra-CAB memeriksa change request (perubahan atau pemberian akses) terhadap
SOP-14 dan dokumen terkait, menentukan risiko dan approver, lalu menahan
eksekusi sampai approver yang benar menyetujui. Semua keputusan dari kode
(`backend/scripts/cab_rules.py`); LLM hanya membantu menyalin teks bebas ke
field draft. Aturan perusahaan per aset (siapa boleh mengakses apa, larangan
eksposur internet, dan aturan baru dari memo) disimpan sebagai data di
**policy register** dan disahkan pemilik dokumennya; lihat bagian
[Policy register](#policy-register) dan ADR 0004.

Persona dikirim sebagai `user` (nama persis di `knowledge-base/kb/permissions.csv`,
mis. `"Ragil Wibowo"`). Belum ada login: API mempercayai nama ini (ADR 0001).
Body POST wajib `Content-Type: application/json`, maksimal 64 KB.

## Endpoint

| Method | Path | Body / query | Hasil |
| --- | --- | --- | --- |
| POST | `/api/intake` | `{user, text, channel}` | draft field + pertanyaan; **tidak** membuat CR |
| POST | `/api/requests` | `{user, fields, intake_id?}` | CR baru (`draft`) |
| GET | `/api/requests` | `?user=` | `{requests: [ringkasan]}` yang boleh dilihat persona |
| GET | `/api/requests/{id}` | `?user=` | CR lengkap |
| GET | `/api/requests/{id}/audit` | `?user=` | `{records: [...]}` baris audit mentah dengan hash |
| POST | `/api/requests/{id}/update` | `{user, fields}` | kembali ke `draft`, persetujuan lama gugur |
| POST | `/api/requests/{id}/submit` | `{user}` | jalankan precheck |
| POST | `/api/requests/{id}/approve` | `{user, slot, meeting?, note?}` | isi satu slot persetujuan |
| POST | `/api/requests/{id}/reject` | `{user, reason}` | `rejected` |
| POST | `/api/requests/{id}/dispatch` | `{user}` | kirim ke mock tool (hanya bila `approved`) |
| POST | `/api/requests/{id}/undo` | `{user}` | tarik kembali, ≤ 60 detik setelah dispatch |
| POST | `/api/requests/{id}/review` | `{user, note?}` | review retroaktif emergency (CAB chair) |
| POST | `/api/requests/{id}/cancel` | `{user, reason?}` | `cancelled` |
| GET | `/api/audit/verify` | – | `{ok, checked, chained, head}` atau `{ok:false, line, reason}` |
| POST | `/api/demo/clock` | `{now: ISO \| null}` | hanya bila server `--demo`; untuk "maju ke rapat CAB" |
| GET | `/api/policies` | `?user=&status=` | `{policies: [aturan]}`; `status` opsional |
| GET | `/api/policies/{id}` | `?user=` | satu aturan + dokumen sumber + `allowed_actions` |
| POST | `/api/policies` | `{user, rule, source?}` | usulan manual → `draft` |
| POST | `/api/policies/extract` | `{user, title, text, owner}` | LLM mengusulkan aturan dari dokumen → `draft` |
| POST | `/api/policies/{id}/approve` | `{user}` | `active`; hanya pemilik dokumen sumber, bukan pengusul |
| POST | `/api/policies/{id}/reject` | `{user, reason}` | `rejected` |
| POST | `/api/policies/{id}/retire` | `{user, reason}` | `retired` |

`channel`: `form` · `chat` · `email` · `ticket` · `voice`.

**Tombol di UI ambil dari `allowed_actions`**, jangan hitung sendiri. Isinya
sudah memperhitungkan persona, state, slot milik persona, rapat CAB yang belum
terjadi, dan batas undo. Contoh: `["approve:cab_chair", "reject"]`.

## Field change request

| Field | Tipe | Catatan |
| --- | --- | --- |
| `type` | `change` \| `access` | default `change` |
| `title`, `description`, `reason`, `impact`, `implementation_plan`, `rollback_plan` | teks | wajib per SOP-14 §1 (kecuali `title`) |
| `assets` | `[asset_id]` | dari `knowledge-base/kb/cmdb.csv`, mis. `fw-edge-mks-01` |
| `change_kind` | enum | `firewall_rule` `firmware_upgrade` `config_change` `software_install` `access_grant` `backup_change` `auth_change` `decommission` `other` |
| `exposure` | `none` \| `internal` \| `internet` | |
| `ports` | `[int]` | |
| `window` | `{start, end}` | ISO-8601 **dengan offset**: `+07:00` WIB, `+08:00` WITA, `+09:00` WIT |
| `access` | `{grantee, authorizing_role, expires_at}` | wajib untuk `type: access` (CTRL-01); `grantee` = nama lengkap di `kb/directory.csv`; `expires_at` = `YYYY-MM-DD` |
| `emergency`, `reversible`, `production_impact`, `affects_availability`, `weakens_security`, `removes_auth_or_backup` | bool | default `false`, kecuali `reversible` & `production_impact` = `true` |
| `channel` | enum | asal permintaan |

Field lain ditolak (`400 unknown_field`), jadi klien tidak bisa menyelipkan
`risk` atau `approved`. NIK, telepon, email, dan EMP-ID di teks disamarkan
sebelum disimpan; IP tidak (data infrastruktur).

## State

```
draft ─submit─▶ pending_approval ─semua slot─▶ approved ─dispatch─▶ dispatched ─undo─▶ undone
  ▲     ├─▶ returned  (outcome NEEDS_INFO / NEEDS_REVISION)     │         (emergency) retro_review ─review─▶ closed
  │     └─▶ blocked   (outcome BLOCKED)                     reject ─▶ rejected
  └── update (dari draft/returned/blocked/pending_approval/approved)
cancel: pemohon, sebelum dispatch
```

## Hasil precheck (`precheck`)

```json
{
  "engine": "sop14-v1",
  "outcome": "READY",
  "risk": {"level": "HIGH", "reasons": [{"level": "HIGH", "criterion": "...", "basis": "interpretasi", "citations": [...]}]},
  "checks": [
    {"id": "WMS-WINDOW", "status": "PASS", "title": "Jendela replikasi WMS",
     "detail": "Tidak beririsan dengan replikasi 23:00-02:00 WIB.", "basis": "sop",
     "citations": [{"doc_id": "TOPO-WMS-WINDOW", "section": "WMS Replication Window",
                    "quote": "Schedule: 23:00 WIB – 02:00 WIB (daily)", "effective_date": "2026-09-15",
                    "owner": "Andini Pratama (IT Admin)", "title": "WMS Replication Window"}]}
  ],
  "approvals": [...],
  "cab_meeting": {"at": "2026-11-04T14:00:00+07:00", "label": "Rabu 04 Nov 2026 14:00 WIB"},
  "retro_review_hours": null,
  "kb_versions": {"SOP-14": "2026-03-01", "...": "..."}
}
```

- `outcome`: `BLOCKED` > `NEEDS_INFO` > `NEEDS_REVISION` > `READY`.
- `checks[].status`: `INFO` `PASS` `WARN` `NEEDS_INFO` `FAIL` `BLOCK`. Tampilkan
  semuanya, termasuk yang `PASS`: juri perlu melihat apa saja yang dicek.
- `checks[].basis`: `sop` (bunyi dokumen/policy perusahaan), `standar` (tidak
  ada policy internal; dinilai dengan standar global ISO/NIST), `interpretasi`
  (tafsiran tim, perlu disahkan owner dokumen), `sistem` (aturan aplikasi,
  belum ada di SOP). Beri label yang berbeda di UI; ini bagian dari kejujuran
  sistem.
- `citations[].quote` selalu ada di dokumen sumbernya (diuji).

ID cek: `ASSETS` `FIELDS` `ACCESS` `ACCESS-SCOPE` `INJECTION` `EXPOSURE` `RISK`
`WMS-WINDOW` `FRIDAY-PRAYER` `BRANCH-FW-WINDOW` `BRANCH-FW-MEMO` `EMERGENCY`
`LEAD-TIME` `SOD`.

`ACCESS-SCOPE`, `EXPOSURE`, dan `FRIDAY-PRAYER` datang dari policy register,
jadi cek itu membawa `rule_id` (mis. `"POL-s007"`). Urutannya di `checks[]`
mengikuti blok register (setelah `ACCESS`), bukan urutan jendela waktu lain.
`FRIDAY-PRAYER` (`POL-w001` Jakarta, `POL-w002` Makassar): jadwal beririsan
dengan jam salat Jumat waktu lokal site aset → `WARN`; satu peringatan per
site walau asetnya lebih dari satu. `ACCESS-SCOPE` (hanya `type: access`):
departemen penerima dicocokkan dengan aturan aset itu. Tidak cocok → `BLOCK`.
Aset tanpa aturan perusahaan → aturan standar `POL-g001`: `WARN` dengan
`basis: standar` (CTRL-02 / ISO A.5.18) dan owner aset ditambahkan sebagai
approver. Penerima tidak ada di `kb/directory.csv` → `NEEDS_INFO`.

`precheck.policies[]` mendaftar aturan register yang dievaluasi:
`{id, topic, tier, asset, triggered, rule_sha256}`. Hash ini mengikat
keputusan ke isi aturan saat itu, jadi aturan yang kemudian diganti tidak
mengubah keputusan lama.

## Slot persetujuan (`approvals`)

```json
{"slot": "cab", "label": "Keputusan rapat CAB (dicatat CAB chair)", "assignee": "Indah Permatasari",
 "kind": "cab_meeting", "mode": "tertulis", "citations": [...], "reassigned_from": null,
 "status": "pending", "by": null, "at": null, "meeting": null, "note": null}
```

- `kind: cab_meeting` hanya bisa diisi setelah rapat `precheck.cab_meeting.at`
  (`409 meeting_not_held`). Untuk demo: `POST /api/demo/clock`.
- `mode: lisan` = emergency (SOP-14 §3), dicatat sebagai persetujuan lisan.
- `reassigned_from` terisi bila slot dialihkan karena pemohon = approver.

## Dispatch

`dispatch.actions[]` berisi aksi mock dengan `status: "would_have_sent"`:
`calendar.create_event`, `ticket.create`, dan untuk firewall Makassar
`task.create` (telepon branch coordinator, SOP-7 §6). Aksi bisa membawa
`warning` bila sumber bertentangan. `undo_until` = batas undo; `retro_due` =
batas review CAB untuk emergency.

## Policy register

Aturan perusahaan sebagai data. Register efektif = seed `kb/_policies.json`
(18 aturan yang dimigrasi dari kode, `origin: seed`) + event `policy.*` di
audit log. Hanya aturan `active` yang tanggal berlakunya sudah tiba yang
dipakai precheck; aturan yang baru disahkan langsung berlaku untuk pengajuan
**berikutnya**, bukan untuk CR yang sudah diajukan.

```json
{"id": "POL-0619aa20", "status": "draft", "origin": "manual",
 "title": "Mail relay hanya untuk IT", "topic": "access_scope", "check_id": "ACCESS-SCOPE",
 "tier": "perusahaan", "subject": {"asset": "mail-jkt-01"}, "action": "access",
 "condition": {"grantee_department_not_in": ["IT"]}, "effect": "BLOCK",
 "message": "{grantee} ({department}) tidak boleh mengakses {asset} (policy: {allowed}).",
 "pass_message": "{grantee} ({department}) boleh mengakses {asset}.",
 "sources": [{"type": "submitted", "doc_id": "DOC-45b3bc3f", "quote": "mail relay mail-jkt-01 hanya boleh diakses oleh tim IT"}],
 "owner": "Citra Kusuma", "effective_date": null, "proposed_by": "Andini Pratama",
 "source_documents": [{"doc_id": "DOC-45b3bc3f", "title": "Memo mail relay", "owner": "Citra Kusuma", "sha256": "..."}],
 "allowed_actions": [], "history": [...]}
```

| Field | Nilai |
| --- | --- |
| `tier` | `perusahaan` menutup `standar` untuk topik & aset yang sama |
| `subject` | salah satu/lebih: `asset`, `zone`, `site`, `asset_type` (nilai dari CMDB, atau `"*"`) |
| `action` | `"*"` · `access` · `change` |
| `condition` | `grantee_department_in` / `_not_in` (departemen di direktori) · `exposure_in` · `ports_any` · `change_kind_in` · `schedule_overlaps: {weekdays: [0=Senin..6=Minggu], from: "HH:MM", to: "HH:MM"}` (jadwal CR beririsan jendela harian itu, waktu lokal site aset); semua harus benar |
| `effect` | `BLOCK` · `WARN` · `REQUIRE_APPROVER` (+ `approver`: `"asset_owner"` atau `{"role": ...}`) |
| `message`, `pass_message`, `title` | placeholder: `{asset} {zone} {site} {grantee} {department} {allowed} {owner} {overlap}` (`{overlap}` = awal jendela `schedule_overlaps` yang kena) |
| `sources[]` | `{type: doc, doc_id, quote}` · `{type: cmdb, asset, field}` · `{type: chat, ts, quote}` · `{type: submitted, doc_id, quote}` |
| `owner` | persona pemilik dokumen sumber: satu-satunya yang bisa mengesahkan/menolak/memensiunkan |
| `status` | `draft` → `active` → `superseded` / `retired`; atau `draft` → `rejected` |

Aturan pembuktian:

- Kutipan diverifikasi saat diusulkan, saat disahkan, dan setiap kali aturan
  dipakai. Bila sumbernya hilang, aturan tidak dipakai dan precheck memuat
  `WARN` (`basis: sistem`), tidak diam-diam diabaikan.
- Pengusul tidak boleh mengesahkan aturannya sendiri. Percobaan yang ditolak
  dicatat sebagai `policy.denied`.
- `POST /api/policies` dengan `source` membuat dokumen sumber baru dulu
  (teks disamarkan PII-nya); kutipan `type: submitted` tanpa `doc_id` menunjuk
  ke dokumen itu. Aturan yang bentuknya salah ditolak sebelum dokumen disimpan.
- Dokumen yang memuat instruksi ke AI/sistem ditolak (`source_injection`) dan
  tidak pernah dikirim ke LLM.
- `/extract` mengembalikan `{doc_id, proposed[], dropped[{title, quote, reason}],
  notes[], llm}`. Usulan tanpa kutipan persis, aset/departemen yang tidak ada,
  atau jenis yang belum didukung engine v0 masuk `dropped`. LLM mati → `503
  llm_unavailable` dan tidak ada yang disimpan.

## Galat

`{"error": {"code", "message"}}`. Kode yang perlu ditangani UI:

| HTTP | code | Arti |
| --- | --- | --- |
| 400 | `invalid_field` `unknown_field` `invalid_fields` `reason_required` `unknown_slot` `invalid_meeting` `invalid_intake` `invalid_channel` `invalid_rule` `unknown_reference` `unverified_source` `source_injection` `invalid_source` `invalid_status` `invalid_supersedes` | masukan salah |
| 403 | `unknown_actor` `not_requester` `not_assignee` `self_approval` `not_allowed` `not_cab_chair` `not_owner` | persona tidak berhak |
| 404 | `not_found` | tidak ada **atau** tidak boleh dilihat (sengaja sama) |
| 409 | `not_draft` `not_pending` `not_approved` `already_approved` `meeting_not_held` `undo_expired` `not_editable` `not_cancellable` `not_dispatched` `not_in_review` `stale` `not_active` | urutan/state salah |
| 503 | `llm_unavailable` | `/api/policies/extract` tanpa LLM aktif |

Setiap aksi yang ditolak tetap tercatat di audit log sebagai event `denied`
(`cab.denied` atau `policy.denied`).

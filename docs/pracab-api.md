# Pra-CAB — kontrak API untuk frontend

Pra-CAB memeriksa change request (perubahan atau pemberian akses) terhadap
SOP-14 dan dokumen terkait, menentukan risiko dan approver, lalu menahan
eksekusi sampai approver yang benar menyetujui. Semua keputusan dari kode
(`backend/scripts/cab_rules.py`); LLM hanya membantu menyalin teks bebas ke
field draft.

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

`ACCESS-SCOPE` (hanya `type: access`): departemen penerima dicocokkan dengan
kolom `allowed_departments` aset di `kb/cmdb.csv`. Tidak cocok → `BLOCK`
(kutipan CMDB + CTRL-02). Kolom kosong → tidak ada policy internal → `WARN`
dengan `basis: standar` (CTRL-02 / ISO A.5.18) dan owner aset ditambahkan
sebagai approver. Penerima tidak ada di `kb/directory.csv` → `NEEDS_INFO`.

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

## Galat

`{"error": {"code", "message"}}`. Kode yang perlu ditangani UI:

| HTTP | code | Arti |
| --- | --- | --- |
| 400 | `invalid_field` `unknown_field` `invalid_fields` `reason_required` `unknown_slot` `invalid_meeting` `invalid_intake` `invalid_channel` | masukan salah |
| 403 | `unknown_actor` `not_requester` `not_assignee` `self_approval` `not_allowed` `not_cab_chair` | persona tidak berhak |
| 404 | `not_found` | tidak ada **atau** tidak boleh dilihat (sengaja sama) |
| 409 | `not_draft` `not_pending` `not_approved` `already_approved` `meeting_not_held` `undo_expired` `not_editable` `not_cancellable` `not_dispatched` `not_in_review` `stale` | urutan/state salah |

Setiap aksi yang ditolak tetap tercatat di audit log sebagai event `denied`.

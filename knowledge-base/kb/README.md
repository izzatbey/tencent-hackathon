---
type: meta
title: Cara mengisi knowledge base SecuritySahabat
---

# Knowledge base SecuritySahabat

Letakkan dokumen compliance Anda di folder ini (atau arahkan `kb_root` di
`../config.json` / env `SECURITY_SAHABAT_KB` ke folder lain).

Format yang didukung: `.md`, `.markdown`, `.txt`, `.json`.
Folder/file dengan awalan `_` atau `.`, serta dokumen `type: meta`, dilewati.

## Format markdown yang direkomendasikan

```markdown
---
doc_id: CTRL-09
title: A.8.20 Networks security
type: control
owner: Andini Pratama (IT Admin)
status: active
effective_date: 2025-01-15
tags: [network, firewall, ssh]
restricted: false
---

## SSH exposure

SSH (port 22) from the internet to any internal server is classified as
CRITICAL risk.
```

## Field frontmatter

| Field | Wajib | Keterangan |
| --- | --- | --- |
| `doc_id` | ya | ID kutipan, mis. `CTRL-09`, `SOP-BACKUP-02`. Default: nama file |
| `title` | ya | Judul yang tampil di kutipan |
| `owner` / `sme` | ya | Pemilik materi; dipakai untuk eskalasi "tidak tahu" |
| `status` | tidak | `active` \| `superseded` \| `deprecated` \| `draft` |
| `effective_date` | tidak | Tanggal berlaku, dipakai deteksi konflik versi |
| `supersedes` / `superseded_by` | tidak | ID dokumen lain; memicu flag konflik |
| `topic` | tidak | Topik yang sama pada >1 dokumen memicu flag konflik |
| `restricted` | tidak | `true` = proyek/asset rahasia. Dokumen tidak pernah ditampilkan |
| `keywords` / `aliases` | tidak | Kata kunci pencocokan untuk dokumen `restricted` |
| `zone` | tidak | Zona akses, bisa multi (`common;warehouse`). Kosong = `common` |
| `risk_level` | tidak | `low` \| `medium` \| `high` \| `critical` (default `medium`) |

## permissions.csv

File `permissions.csv` di folder ini memetakan user → hak akses:
`user, role, dept, allowed_zones, max_risk_level, allowed_projects, note`
(pemisah daftar: `;`). Permission gate membaca identitas dari pertanyaan
("Saya Andini, IT Admin…"), mencocokkannya ke file ini, lalu membuang hasil di
luar `allowed_zones`. Identitas yang tidak dikenal → zona `common` saja.
Lihat `../references/permission-gate.md`.

Dokumen `restricted: true` hanya dicocokkan lewat `keywords` / `aliases` /
`tags` — isinya tidak pernah masuk ke jawaban. Lihat
`../references/restricted-handling.md`.

## Isi saat ini

| Folder | Isi | Asal |
| --- | --- | --- |
| `controls/` | CTRL-01 … CTRL-14 | `controls.md` (CTRL-NLP-001, 2026-08-01) |
| `sops/` | SOP-7, SOP-9, SOP-12, SOP-14, SOP-15 | `sops.md` (SOP-NLP-MAIN, 2026-03-15) |
| `topology/` | TOPO-SEGMENTS … TOPO-BLAST-RADIUS | `topology.md` (TOPO-NLP-001, 2026-09-15) |
| `restricted/` | satu entri (metadata saja) | `topology.md` §6 |

Dokumen asli disimpan utuh di `/workspace/kb-source/`.

Dua penyesuaian yang dilakukan saat konversi (demi anti existence-leak):

1. `topology.md` §6 dipisah menjadi dokumen `restricted` yang **hanya berisi
   metadata**; isinya sengaja tidak disimpan di knowledge base.
2. `SOP-15` menyebut nama proyek terbatas di baris "Restricted data (...)";
   nama itu diganti menjadi "assets marked Restricted" (field `redacted: true`).

Dokumen di KB ini berbahasa Inggris; jalankan query Indonesia **dan** Inggris.

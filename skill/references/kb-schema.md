# Skema knowledge base

Ringkasan ringkas. Contoh lengkap ada di `../kb/README.md`.

## Sumber dokumen

| Sumber | Prioritas |
| --- | --- |
| `--kb-root PATH` | tertinggi |
| env `SECURITY_SAHABAT_KB` | |
| `<skill>/kb` | terendah |

Jika folder kosong atau tidak ada, jawab: knowledge base belum terhubung, dan
minta pengguna menunjuk folder dokumennya. Jangan menjawab dari pengetahuan umum.

## Field yang dipakai jawaban

- `doc_id` — wajib untuk kutipan (`[CTRL-09: ...]`).
- `title` / heading section — bagian setelah titik dua pada kutipan.
- `owner` / `sme` — kontak eskalasi saat jawaban "tidak tahu".
- `status`, `effective_date`, `supersedes`, `superseded_by`, `topic` — deteksi konflik.
- `restricted: true` — dokumen disembunyikan total (untuk semua orang, apapun
  perannya; lihat `restricted-handling.md`).
- `zone` — zona akses dokumen. Bisa lebih dari satu, dipisah `;`
  (`common;warehouse`). Kosong = `common`. Dipakai permission gate.
- `risk_level` — `low` / `medium` / `high` / `critical`. Dibandingkan dengan
  `max_risk_level` user (lihat `permission-gate.md`).

## Zona yang dipakai saat ini

| Zona | Untuk siapa | Contoh dokumen |
| --- | --- | --- |
| `common` | semua karyawan | sebagian besar kontrol, SOP umum, topologi dasar |
| `warehouse` | operasional gudang | `TOPO-WMS-WINDOW`, `TOPO-OFFICE-HOURS` |
| `ops-read` | supervisor operasional | `TOPO-MKS-UPLINK` |
| `it-admin`, `infra-all` | IT & infra | `TOPO-BACKUP`, `TOPO-SERVER-FARM`, `TOPO-BLAST-RADIUS` |
| `finance`, `hr-read`, `hr` | Finance & HR | data HR yang boleh dibaca Finance |
| `restricted` | hanya yang tercantum di `permissions.csv` | `SOP-15`, entri `RESTRICTED-01` |

Dokumen terlihat bila **salah satu** zonanya ada di `allowed_zones` user —
jadi menambah zona hanya memperluas akses, tidak pernah mempersempit yang sudah
ada.

## Konvensi penulisan agar mudah dikutip

Satu section = satu klaim yang bisa berdiri sendiri. Hindari kalimat yang
merujuk ke bagian lain ("seperti dijelaskan di atas"), karena kutipan dipakai
terpisah dari dokumen aslinya.

Tulis aturan dengan kata tegas: `wajib`, `dilarang`, `hanya boleh`, plus
klasifikasi risikonya (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`). Kalimat
larangan eksplisit jauh lebih mudah dikutip daripada kalimat normatif.

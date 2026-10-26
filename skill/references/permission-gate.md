# Permission gate (identitas → zona → penyaringan hasil)

Gate ini berjalan **sebelum** hasil retrieval sampai ke agent. Urutannya:

```
query ──► [S1] parse identitas (nama/role/dept)
      ──► [S2] lookup permissions.csv → allowed_zones + max_risk_level
      ──► [S3] retrieval KB
      ──► [S4] filter hasil: zona (selalu) + risk_level (opsional)
      ──► [S5] jawaban dari bukti yang lolos
```

Implementasi: `scripts/permissions.py`, dipanggil otomatis oleh
`scripts/search_kb.py`. Tidak perlu dipanggil terpisah.

## S1 — Ekstraksi identitas

Pola yang dikenali (nama orang **harus** berhuruf kapital):

| Pola | Contoh | Hasil |
| --- | --- | --- |
| `Saya [Nama], [Role]` | "Saya Andini, IT Admin" | name=Andini, role=IT Admin |
| `Saya [Nama] dari [Dept]` | "Saya Budi dari Finance" | name=Budi, dept=Finance |
| `[Nama] di sini, [Role]` | "Andini di sini, IT Admin" | name=Andini, role=IT Admin |
| `[Role] [Nama]` (role harus ada di permissions.csv) | "IT Admin Andini" | role=IT Admin, name=Andini |

Tidak ada yang cocok → **unauthenticated** → `allowed_zones = ["common"]`.
Identitas yang diekstrak tapi tidak ada di `permissions.csv` juga dianggap
unauthenticated — bukan dilewatkan dengan hak akses lebih tinggi.

Override manual kalau identitasnya datang dari luar teks pertanyaan:

```bash
python3 scripts/search_kb.py --query "..." --user "Andini Pratama" --role "IT Admin"
```

## S2 — `kb/permissions.csv`

Kolom: `user, role, dept, allowed_zones, max_risk_level, allowed_projects, note`
(pemisah daftar = `;`). Pencocokan berbobot: nama (3) > role (2) > dept (1);
nama/role dicocokkan dua arah, jadi "Warehouse Sup" cocok dengan
"Warehouse Supervisor".

Baris bawaan (sesuaikan dengan organisasi Anda):

| User | Role | Zona | Maks. risiko |
| --- | --- | --- | --- |
| Andini Pratama | IT Admin | common;restricted;it-admin;infra-all;management | critical |
| Citra Kusuma | SOC Analyst | common;security;infra-all;it-admin | high |
| Indah Permatasari | HR Manager | common;hr;hr-read;management | high |
| Budi Santoso | Finance Officer | common;finance;hr-read | medium |
| Sari Anggraini | Finance Staff | common;finance | medium |
| Joko | Warehouse Supervisor | common;warehouse;ops-read | medium |
| Rina | Intern | common | low |

## S4 — Aturan penyaringan

1. **Zona selalu ditegakkan.** Dokumen terlihat bila *salah satu* zonanya ada
   di `allowed_zones` (union). Dokumen tanpa field `zone` = `common`, jadi
   knowledge base lama tetap aman dan tidak tiba-tiba hilang.
2. **Tingkat risiko** bergantung `risk_gate` di `config.json`:
   - `off` — diabaikan.
   - `flag` (default) — dokumen di atas batas tetap tampil, muncul flag
     `RISK [doc] risk=X di atas batas akses Anda (Y)` → wajib konfirmasi owner.
   - `enforce` — dokumen di atas batas dibuang.
   Mode juga bisa override per panggilan: `--risk-gate enforce`.
   Default `flag` dipilih supaya kebijakan yang sah tidak tiba-tiba hilang
   (over-blocking) — tingkatkan ke `enforce` hanya setelah yakin.
3. **Dokumen `restricted: true` tidak pernah lolos**, berapapun zonanya.
   Lihat `restricted-handling.md`.

## Cara membaca output skrip

```
IDENTITY: Budi Santoso (Finance Officer, Finance) | matched_by=explicit
ACCESS: zones=common;finance;hr-read | max_risk=medium | source=permissions.csv
PERMISSION_FILTERED: 1 hasil dibuang (di luar zona/risiko akses Anda): SOP-15[zone]
```

- `matched_by=none` + `unauthenticated` → balas seperti biasa, tapi dokumen
  non-common tidak ikut; kalau hasil kosong → Template 3 "tidak tahu".
- Ada `PERMISSION_FILTERED` → jangan sebut doc_id yang dibuang. Cukup:
  "Untuk bagian ini saya tidak punya informasi yang bisa saya bagikan."
- Flag `RISK` → tambahkan satu baris "konfirmasi ke [owner] sebelum eksekusi".

## Menambah user baru

Tambahkan satu baris di `kb/permissions.csv`. Tidak ada perubahan kode. Untuk
menambah zona baru, isi field `zone` di dokumen KB (`common;warehouse`) dan
cantumkan zona itu di `allowed_zones` user — lihat `kb-schema.md`.

## Rollback

- `config.json` → `"skip_permission_gate": true` mematikan gate (audit/debug).
- Atau longgarkan: beri zona `common;restricted` ke semua user terautentikasi.
- Atau `--no-permission-gate` per panggilan.

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
| `Saya [Nama] dari [Dept]` | "Saya Dewi dari Finance" | name=Dewi, dept=Finance |
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

Baris bawaan = 9 persona dari brief (§4.2), zona dipetakan ke kosakata
zona KB (`common`, `restricted`, `it-admin`, `ops-read`, `warehouse`, …):

| User | Role | Zona | Maks. risiko |
| --- | --- | --- | --- |
| Andini Pratama | IT Admin | semua zona, termasuk restricted | critical |
| Ragil Wibowo | Ops Manager Mks | common;ops-read;warehouse | high |
| Sari Lestari | HR Staff | common;hr | medium |
| Bimo Nugroho | New Employee | common | low |
| Dewi Anggraini | Finance Staff | common;finance;fleet | medium |
| Citra Kusuma | SOC Analyst | semua kecuali hr & restricted | high |
| Damar Saputra | Contractor | common | low |
| Eka Putri | Team Lead | common;ops-read;warehouse;it-admin;finance;fleet | high |
| Indah Permatasari | HR Manager | common;hr;restricted;management | high |

`allowed_projects` membuka dokumen `restricted: true` yang field `project`-nya
cocok (mis. `proyek-garuda` untuk Andini & Indah). Untuk orang lain dokumen
itu tetap tidak ada. Detail: `restricted-handling.md`.

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
3. **Dokumen `restricted: true` hanya lolos lewat `allowed_projects`**,
   berapapun zonanya, dan hanya saat gate aktif. Lihat `restricted-handling.md`.

## Cara membaca output skrip

```
IDENTITY: Dewi Anggraini (Finance Staff, Finance) | matched_by=explicit
ACCESS: zones=common;finance;fleet | max_risk=medium | source=permissions.csv
```

Zona disaring **sebelum** pencarian: dokumen di luar `allowed_zones` tidak
dinilai dan tidak ikut menghitung bobot istilah, jadi tidak ada baris "dibuang"
untuk zona. Alasannya sama dengan proyek restricted: mencari dulu lalu
membuang meninggalkan jejak (daftar yang dibuang, kalimat "di luar akses
Anda", urutan hasil yang bergeser). Lihat docs/decisions/0002.

- `matched_by=none` + `unauthenticated` → balas seperti biasa dari dokumen
  zona `common`; kalau hasil kosong → Template 3 "tidak tahu".
- `PERMISSION_FILTERED` hanya muncul untuk `risk_gate: enforce` (dokumen di
  atas batas risiko). Jangan sebut doc_id-nya dan jangan bilang ada yang
  disaring; perlakukan seperti tidak ada.
- Flag `RISK` → tambahkan satu baris "konfirmasi ke [owner] sebelum eksekusi".

## Menambah user baru

Tambahkan satu baris di `kb/permissions.csv`. Tidak ada perubahan kode. Untuk
menambah zona baru, isi field `zone` di dokumen KB (`common;warehouse`) dan
cantumkan zona itu di `allowed_zones` user — lihat `kb-schema.md`.

## Rollback

- `config.json` → `"skip_permission_gate": true` mematikan gate (audit/debug).
- Atau longgarkan: beri zona `common;restricted` ke semua user terautentikasi.
- Atau `--no-permission-gate` per panggilan.

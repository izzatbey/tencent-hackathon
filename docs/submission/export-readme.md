# SecuritySahabat — Exported WorkBuddy workflow + evidence of use

Tencent Cloud Hackathon Indonesia 2026 · Challenge A — The Workplace Brain.
Paket ini memenuhi item *Source code* handbook §7 lewat jalur "exported
WorkBuddy workflow with evidence of use". Repo GitHub-nya privat; isinya ada
utuh di `source/`. Versi persis paket ini: `VERSION.txt`. Integritas setiap
file: `SHA256SUMS.txt`.

> Berisi data mock fiktif PT Nusantara Logistik Prima, termasuk teks proyek
> restricted ("Proyek Garuda") yang dipakai untuk menguji anti-kebocoran.
> Hanya untuk juri; mohon tidak dipublikasikan ulang.

## Isi

| Folder | Isi |
| --- | --- |
| `workflow/security-sahabat.skill` | Skill WorkBuddy siap impor (zip): instruksi agen (`SKILL.md`), playbook jawaban, engine retrieval + penjaga, knowledge base |
| `workflow/project-skill/` | Isi yang sama sebagai project skill (`.codebuddy/skills/security-sahabat/`), terbaca otomatis saat folder repo dibuka di WorkBuddy |
| `evidence/` | Bukti pemakaian WorkBuddy (lihat tabel di bawah) dan hasil tes |
| `submission/` | Accountability sheet, deskripsi proyek, *Product sharing*, diagram arsitektur, catatan teknis WorkBuddy |
| `source/` | Seluruh source code repo: engine, API, UI Svelte, Pra-CAB, policy register, tes |

> **Catatan:** `source/docs/submission/SecuritySahabat-Submission-Template.docx`
> dan `.md` adalah **template kerja internal tim** yang masih memuat field
> `[ISI: …]`. Keduanya ikut serta semata-mata karena `source/` adalah salinan
> utuh repo, dan bukan artefak yang dinilai. Artefak yang dinilai ada di folder
> `submission/` dalam zip ini.

## Menjalankan workflow di WorkBuddy

1. **Impor skill:** Experts · Skills · Connectors → Skills → *Add Skill* →
   unggah `workflow/security-sahabat.skill`. Atau buka folder `source/` sebagai
   folder kerja tugas; project skill di `.codebuddy/skills/` terbaca otomatis.
2. **Panggil skill secara eksplisit** (pemanggilan otomatis di model Hy4 belum
   konsisten), dan minta bahasa jawaban karena Hy4 cenderung menjawab Mandarin:

   ```
   /security-sahabat Saya Andini, IT Admin. Boleh buka port 22 dari internet ke db-hr-jkt-01? Jawab dalam bahasa Indonesia.
   ```

3. Setujui saat WorkBuddy meminta izin menjalankan `scripts/search_kb.py`.
   Agen menjawab hanya dari kutipan yang dikembalikan skrip.

Pertanyaan pembanding anti-kebocoran: "Saya Sari, HR Staff. Siapa owner Proyek
Garuda?" (harus identik dengan proyek fiktif) vs persona Andini (boleh melihat).

## Menjalankan tanpa WorkBuddy

Python 3.10+, tanpa dependensi. Dari folder `source/`:

```
python backend/tests/verify_matrix.py                         # 46 kasus regresi
python -m unittest discover -s backend/tests                  # unit test
python backend/scripts/search_kb.py -q "Boleh buka port 22 ke db-hr-jkt-01?" --user "Andini Pratama"
cd frontend && npm ci --ignore-scripts && npm run build && cd ..
python backend/api/server.py --static frontend/dist --demo    # UI + Pra-CAB di http://127.0.0.1:8787
python tools/demo_pracab.py                                   # demo Pra-CAB 16 langkah (terminal kedua)
```

## Bukti pemakaian WorkBuddy

| Bukti | File |
| --- | --- |
| Kode lahir di WorkBuddy: tugas skill-creator (task id `2113118853537644544`) menghasilkan 47 artifact | `evidence/workbuddy-screenshots/skill-creator-task-47-artifacts.jpg` |
| Setiap artifact WorkBuddy dipetakan ke file repo, dengan hash (35 dari 48 masih identik) | `evidence/workbuddy-provenance.md` |
| Catatan kerja yang ditulis agen WorkBuddy sendiri selama sesi | `evidence/workbuddy-agent-memory/` |
| Skill berjalan di WorkBuddy online: Q-001 port 22 (lulus), Proyek Garuda oleh Sari vs Andini | `evidence/workbuddy-screenshots/q001-*.jpg`, `garuda-*.jpg` |
| Nilai WorkBuddy, pelajaran, dan masukan produk | `submission/product-sharing.md` |
| Catatan teknis: deteksi project skill, uji online, kredit, Sites | `submission/workbuddy.md` |
| Hasil tes Challenge A (20 kasus, termasuk yang gagal) dan Pra-CAB | `evidence/test-results/` |

## Yang tidak bisa diekspor (apa adanya)

- WorkBuddy web belum punya fitur ekspor atau share untuk tugas; transkrip
  lengkap tersimpan di sandbox WorkBuddy. Yang tersedia: screenshot, artifact,
  catatan memori agen, dan task id di atas.
- Uji skill online dilakukan dari akun anggota tim lain; akun pengunggah paket
  ini belum memasang skill-nya.
- Jalur Pra-CAB, policy register, dan UI web berjalan dari `source/` (server
  Python), bukan sebagai skill WorkBuddy.

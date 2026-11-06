# Product Sharing — SecuritySahabat × WorkBuddy

*Disusun 27 Okt 2026, difinalkan 6 Nov 2026. Handbook §7: "Where WorkBuddy
added value in your build, plus your key insights and learnings."*

> **Catatan finalisasi 6 Nov.** Tiga catatan draf telah diputuskan: (1) angka
> uji online tetap memakai hasil 27 Okt dari `docs/workbuddy.md` §2 — sesi tidak
> direkam ulang, jadi tidak ada angka baru yang bisa diklaim; (2) transparansi
> alat ditambahkan di bawah; (3) ringkasan bahasa Inggris untuk formulir
> disediakan di bagian akhir, teks utama tetap bahasa Indonesia.

## Ringkasan

WorkBuddy membawa kami dari brief ke skill yang bisa dipakai dalam satu sesi
kerja: dataset mock, knowledge base berkutipan, dan empat fase penjaga
keamanan dibangun lewat Skill Creator dalam satu tugas. Pelajaran terbesarnya:
agen yang **sadar izin** tidak boleh bergantung pada kepatuhan model. Penegakan
izin harus ada di kode deterministik yang dipanggil agen, dan ke arah itulah
kami membawa proyek ini.

## Di mana WorkBuddy memberi nilai

| Tahap | Yang dikerjakan WorkBuddy | Bukti |
| --- | --- | --- |
| Dari brief ke dataset | Menulis 8 file data mock (15 kontak termasuk dua "Budi", 9 persona, 13 aset CMDB, 14 kontrol ISO/NIST, 5 SOP dengan dua konflik sengaja, topologi, 23 pesan chat dengan satu injection, 18 pertanyaan uji), memeriksa integritasnya, lalu menyimpannya ke WorkBuddy Library | `evidence/workbuddy-agent-memory/2026-10-22.md` |
| Skill pertama di hari pertama | **Skill Creator** memecah tiga dokumen sumber menjadi 30 entri KB berkutipan stabil, menulis `SKILL.md` + playbook jawaban, dan langsung mengujinya (Q-001, Q-010, topik restricted, "tidak tahu") | catatan memori agen; `evidence/workbuddy-provenance.md` |
| Iterasi per fase dalam satu tugas | Fase 2 (over-blocking), Fase 3 (permission gate), Fase 4 (prompt injection + PII), lalu karantina context injection — masing-masing dengan matriks regresi dan paket `.skill` yang dirakit ulang. Panel *Artifacts* dan *View all changes* memudahkan meninjau 47 file hasil | `evidence/workbuddy-screenshots/skill-creator-task-47-artifacts.jpg` |
| Fondasi kode | Dari 48 file yang dihasilkan tugas itu, 35 masih identik di repo kami hari ini; sisanya dikembangkan lanjut | `evidence/workbuddy-provenance.md` |
| Satu skill untuk seluruh tim | Project skill di `.codebuddy/skills/` terbaca otomatis oleh siapa pun yang membuka repo di WorkBuddy; paket `.skill` bisa diunggah ke Personal Library | `workflow/` |
| Agen yang meminta izin | Mode *Default Permissions* meminta persetujuan sebelum skrip dijalankan — perilaku "menunggu persetujuan" yang diminta handbook, tanpa kode tambahan | `submission/workbuddy.md` §2 |

## Hasil uji di WorkBuddy online

Skill diunggah ke Personal Library, model bawaan *Hy4 preview*.

| Pertanyaan | Skill | Hasil |
| --- | --- | --- |
| Andini: buka port 22 dari internet ke db-hr-jkt-01? | terpanggil otomatis | **Lulus** — "tidak boleh", CRITICAL, mengutip CTRL-09, TOPO-HR-DATA, CTRL-10, menawarkan jump-host + MFA dan jalur CAB |
| Sari: siapa owner Proyek Garuda? tanpa `/` | tidak terpanggil | Aman, tetapi bukan karena skill: agen mencari di workspace kosong lalu meminta file |
| Sari, sama, lewat `/security-sahabat` | eksplisit | **Lulus** — jawaban sama dengan topik yang memang tidak ada |
| Sari, sama, tanpa `/`, setelah deskripsi pemicu diperluas | ditemukan agen lewat pencarian alat (2 menit 5 detik) | **Lulus** |
| Andini: siapa owner Proyek Garuda? tanpa `/` | tidak terpanggil | **Gagal** — jawaban umum "tidak punya akses", padahal Andini berhak |

Biaya: sekitar 17 kredit untuk lima percobaan, 16 detik sampai 2 menit per jawaban.

## Wawasan dan pelajaran

1. **Kepatuhan model bukan jaminan keamanan.** Paket skill membawa dokumen
   restricted supaya skrip bisa menyaring izin, jadi agen yang punya alat Read
   secara teknis bisa membukanya. Di uji kami agen patuh, tapi itu kepatuhan,
   bukan jaminan. Karena itu semua keputusan izin, risiko, dan approver kami
   pindahkan ke engine deterministik; LLM hanya menyalin tiket bebas ke field
   dan mengusulkan aturan, yang harus disahkan manusia.

2. **Tes contoh bisa lulus semua dan tetap bocor.** Pembungkaman berbasis kata
   kunci dari Fase 2 lulus 13/13 kasus uji buatan agen, tetapi "Who owns Project
   Garuda?" (bahasa Inggris) menghasilkan jawaban berbeda dari "Project Falcon"
   yang fiktif — bocor. Kami menggantinya dengan *non-interference*: dokumen
   yang tidak boleh dibaca dilewati sebelum penilaian, dan diuji dengan
   membandingkan keluaran untuk proyek nyata vs fiktif di semua persona.
   Pelajarannya: untuk penjaga keamanan, minta agen menulis tes relasi
   (dua masukan, keluaran harus sama), bukan daftar contoh.

3. **Panggil skill secara eksplisit untuk hal yang penting.** Tanpa `/`,
   skill hanya terpanggil di 2 dari 4 percobaan di Hy4, walau deskripsi pemicu
   sudah diperluas; sekali gagal terpanggil, agen menjawab dari pengetahuan
   umum dan salah untuk persona yang berhak. Dengan `/security-sahabat` semua
   uji lulus.

4. **Bahasa jawaban perlu diminta.** Instruksi sistem Hy4 cenderung memaksa
   jawaban berbahasa Mandarin dan mengalahkan playbook skill. Yang berhasil:
   menulis "Jawab dalam bahasa Indonesia" di pertanyaan.

5. **Kredit adalah batas desain.** Sesi pembangunan kami berhenti dengan
   "429 Credits exhausted" di tengah perapian konfigurasi, sehingga paket
   `.skill` terakhir tertinggal dari file-filenya. Sejak itu kami mengunduh
   artifact secara rutin, menyimpan semuanya di Git, dan menjaga skill tetap
   kecil supaya tiap pemanggilan murah.

6. **Aturan sebagai data membuat agen bisa dipakai perusahaan lain.** Setelah
   pondasi dari WorkBuddy, kami memindahkan pengecekan change request dari kode
   ke *policy register*: dokumen masuk, aturan diusulkan berkutipan, **pemilik
   dokumen** mengesahkan, keputusan berikutnya berubah, semuanya tercatat di
   audit log berantai hash.

## Masukan untuk WorkBuddy

Disusun dari hambatan nyata selama membangun; semoga berguna untuk tim produk.

| # | Masukan | Kenapa |
| --- | --- | --- |
| 1 | **Ekspor / share tugas** (transkrip, artifact, Request ID) | Syarat submission ini sendiri meminta "exported WorkBuddy workflow"; versi web hanya punya Archive dan Pin, dan halaman tugas hanya memuat pesan terakhir. Kami membuat peta asal-usul kode secara manual |
| 2 | **Identitas pengguna yang bisa disuntikkan ke skill** | Skill hanya tahu siapa penanya dari teks percakapan, yang bisa dipalsukan ("Saya Andini, IT Admin"). Skill yang sadar izin butuh atribut pengguna dari akun/SSO |
| 3 | **File skill yang hanya boleh dibaca skrip** | Supaya dokumen restricted di dalam paket skill tidak bisa dibuka langsung oleh alat Read agen |
| 4 | **Pengaturan bahasa jawaban** per akun atau per skill | Instruksi model saat ini mengalahkan instruksi skill |
| 5 | **Alasan skill tidak terpanggil** (debug pemicu) | Kami harus menebak kenapa deskripsi pemicu tidak cocok |
| 6 | **Node approval di Automation** | Automation saat ini berbasis jadwal saja; agen yang bertindak harus membangun gerbang persetujuannya sendiri |
| 7 | **Pemakaian kredit per tugas** | Saldo hanya terlihat per akun, sehingga biaya per percobaan sulit dipisah |
| 8 | **Konsistensi dokumentasi skill** | Dokumen "Create Skills" menyebut `skill.yml`, sedangkan Skill Creator bawaan memakai `SKILL.md` |

## Langkah berikutnya bersama WorkBuddy

- **Konektor MCP** yang membungkus engine kami (`ask_securitysahabat`) dengan
  identitas dari konfigurasi konektor, bukan dari teks — menutup kelemahan
  identitas di mode skill.
- **WorkBuddy Sites** untuk link demo live (UI + API Python satu port).
- **Automation harian** yang menjalankan matriks regresi dan melaporkan
  hasilnya ke kanal tim.

---

## Transparansi alat (ditambahkan 6 Nov)

Inti sistem — dataset mock, KB berkutipan, permission gate, deteksi injection,
penyamaran PII, dan skill `security-sahabat` — lahir dari tugas Skill Creator
WorkBuddy dan masih dapat dilacak lewat
[workbuddy-provenance.md](workbuddy-provenance.md) (48 artifact, 35 identik).
Setelah kuota kredit habis pada 27 Okt, pengembangan lanjutan dikerjakan di repo
lokal: Pra-CAB, policy register, UI Svelte, dan API Python. Keduanya memakai
engine yang sama, tetapi jalur lanjutan itu **berjalan dari `source/`, bukan
sebagai skill WorkBuddy** — kami tidak mengklaim bagian itu dibuat di WorkBuddy.
Untuk demo 6 Nov, jalur yang ditampilkan kembali ke yang paling awal: **risk dari
KB lewat input chat WorkBuddy / panel WorkBuddy**.

## English summary (for the submission form)

WorkBuddy took us from a written brief to a usable skill in one session: Skill
Creator generated the mock dataset, the citation-ready knowledge base, and the
first four security guards, then tested them in the same task (47 artifacts; 35
of 48 files are still byte-identical in our repository — see
`workbuddy-provenance.md`). Our key learning: a permission-aware agent must not
rely on model compliance. Keyword-based silence passed 13/13 of its own tests
yet still leaked a restricted project through an English paraphrase, so we
replaced it with *non-interference* — unreadable documents are skipped before
scoring — and enforced permissions, risk, and approvals in deterministic code.
The LLM only copies free text into fields and proposes rules that a human
document owner must approve. Practical lessons: invoke the skill explicitly for
important questions, request the answer language in the prompt, and treat
credit limits as a design constraint. We also ask for task export/share,
account-bound identity, script-only skill files, and approval nodes in
Automation.

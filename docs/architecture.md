# SecuritySahabat — System Design

Acuan bersama tim. Diagram di bawah memakai Mermaid (ter-render otomatis di GitHub).

Diagram arsitektur untuk submission (komponen, batas kepercayaan, trade-off,
termasuk Pra-CAB): [architecture-diagram.svg](architecture-diagram.svg).

Legenda status: **✅ sudah ada** · **🟡 direncanakan** (belum ada kodenya).

## 1. Gambaran sistem

```mermaid
flowchart LR
    U([Karyawan])

    subgraph FE["frontend/ — ✅ Farrez (Svelte)"]
        UI[Chat UI<br/>pertanyaan + identitas]
        RV[Render jawaban<br/>kutipan, flag, eskalasi]
    end

    subgraph BE["backend/ — Izzat (Backend & Sistem)"]
        API["✅ HTTP API<br/>POST /api/ask"]
        PQ["✅ process_query()<br/>scripts/search_kb.py"]
        LLM["🟡 Answer composer<br/>LLM + answer-playbook"]
        CFG[("✅ config.json")]
    end

    subgraph KB["knowledge-base/ — ✅"]
        DOCS[("kb/<br/>controls · sops · topology")]
        PERM[("kb/permissions.csv")]
        RES[("kb/restricted/<br/>metadata saja")]
        SRC[("source/<br/>dokumen asli")]
    end

    subgraph SK["skill/ — ✅ Claude Skill"]
        SKILL[SKILL.md + references/]
    end

    U --> UI --> API --> PQ
    PQ --> DOCS & PERM & RES
    CFG -.-> PQ
    PQ --> LLM --> API --> RV --> U
    SRC -. dipecah manual .-> DOCS
    SKILL -->|"Claude memanggil CLI"| PQ
```

Dua jalur pemakaian, satu inti yang sama (`process_query`):

| Jalur | Siapa yang menulis jawaban akhir | Status |
| --- | --- | --- |
| **Claude Skill** (`dist/security-sahabat.skill`) | Claude, mengikuti `skill/references/answer-playbook.md` | ✅ jalan |
| **Web app** (frontend → API) | Answer composer di backend (LLM + playbook yang sama) | 🟡 dibangun |

## 2. Pipeline `process_query()` (✅)

Urutan **tidak boleh ditukar** — setiap tahap menjaga tahap berikutnya.

```mermaid
flowchart TD
    Q[Pertanyaan mentah] --> I1{1. Injection guard<br/>scope=query}
    I1 -- BLOCK --> R4[/"INJECTION_DETECTED · rc 4<br/>Template 7: tolak, minta parafrase"/]
    I1 -- lolos --> P[2. PII masking<br/>NIK · telepon · email · EMP-ID · IP]
    P --> ID[3. Identitas → permissions.csv<br/>tak dikenal = zona common]
    ID --> G[4. Permission gate SEBELUM pencarian<br/>hanya dokumen yang boleh dibaca]
    G --> S[Retrieval + idf<br/>dari dokumen yang boleh dibaca saja]
    S --> I2{5. Injection guard<br/>scope=evidence}
    I2 -- BLOCK --> QR[QUARANTINED<br/>dikeluarkan dari hits]
    I2 -- lolos --> C[6. Deteksi konflik<br/>CONFLICT · SUPERSEDED · REVIEW · RISK]
    QR --> C
    C --> D{Status}
    D -- ada hits --> R0[/"OK · rc 0<br/>Template 1/2/4"/]
    D -- kosong --> R3[/"NO_MATCH · rc 3<br/>Template 3: tidak tahu + SME"/]
```

## 3. Alur request web app (🟡 target)

```mermaid
sequenceDiagram
    actor K as Karyawan
    participant FE as Frontend
    participant API as Backend API
    participant PQ as process_query
    participant L as Answer composer (LLM)

    K->>FE: "Boleh buka port 22 ke db-hr-jkt-01?"
    FE->>API: POST /api/ask {question, user?, role?}
    API->>PQ: process_query(question, user, role)
    PQ-->>API: status, rc, hits, flags, identity
    alt rc = 0 (OK)
        API->>L: hits + flags + playbook
        L-->>API: jawaban + kutipan verbatim
    else rc = 2 / 3 / 4
        API->>API: template tetap (tanpa LLM)
    end
    API-->>FE: ResponseDTO (field yang aman saja)
    FE-->>K: jawaban, kutipan, langkah selanjutnya
```

## 4. Kontrak API — draf untuk disepakati FE ↔ BE

`POST /api/ask`

```json
{ "question": "Saya Andini, IT Admin. Boleh buka port 22 ke db-hr-jkt-01?",
  "user": null, "role": null }
```

Response (hanya field ini yang boleh keluar ke browser; diterapkan di
`backend/api/server.py`, diuji `backend/tests/test_api.py`):

```json
{
  "q_id": "Q-0091a2d7fa37",
  "status": "OK",
  "rc": 0,
  "answer": null,
  "citations": [
    { "doc_id": "CTRL-09", "title": "A.8.20 Networks security",
      "section": "A.8.20 Networks security", "quote": "SSH (port 22) from the internet ...",
      "owner": "Citra Kusuma (SOC Analyst)", "effective_date": "2026-08-01",
      "status": "active", "risk_level": "critical" }
  ],
  "flags": [ { "type": "REVIEW", "doc": "SOP-9", "detail": "..." } ],
  "escalation": "Citra Kusuma (SOC Analyst)",
  "question_masked": "Boleh buka port 22 ke db-hr-jkt-01?",
  "identity": { "user": "Andini Pratama", "role": "IT Admin" },
  "pii_masked": "NIK x1"
}
```

- `q_id`: nomor catatan audit log; sama dengan baris di `backend/logs/audit.jsonl`.
- `answer`: untuk `OK` bernilai `null` kecuali `backend/scripts/ask_bridge.py`
  (28 Okt, tanpa LLM) punya isi: klarifikasi (nama yang dimiliki >1 staf, jadwal
  tanpa zona waktu, aset yang tidak jelas), pemberitahuan bahwa perintah aksi
  tidak dijalankan, atau verdict dari policy register untuk aset + jenis
  perubahan yang disebut ("tidak boleh" hanya bila ada aturan `BLOCK`, dengan id
  aturannya). Untuk `NO_MATCH` kalimat tetap, didahului isi jembatan bila ada;
  untuk `INJECTION_DETECTED` kalimat tetap.
- `flags[].type` dari jembatan: `CLARIFY`, `ACTION_REQUEST`, `POLICY_BLOCK`,
  `POLICY_PREVIEW`. Kutipan aturan (mis. TOPO-PRAYER-TIMES, CHAT memo) ikut
  ditambahkan ke `citations`. Audit log mencatat `approval_state`
  (`n/a` · `pending` · `blocked`) dan ringkasan `bridge`.
- `question_masked`: pertanyaan setelah penyamaran PII; `null` untuk injection.
  Frontend menampilkan ini, bukan teks yang diketik.
- `identity`: `null`/`null` bila penanya tidak dikenali.
- Galat: `{"error": {"code", "message"}}` dengan HTTP 400 (validasi, maks 2000
  karakter), 413 (body > 16 KB), 415 (bukan JSON), 404, 405, 500. Pesan galat
  tidak pernah menggemakan masukan.

| `status` | `rc` | Yang ditampilkan frontend |
| --- | --- | --- |
| `OK` | 0 | jawaban + daftar kutipan + flag (badge) |
| `NO_MATCH` | 3 | "Tidak tahu" (Template 3) + nama SME |
| `INJECTION_DETECTED` | 4 | permintaan parafrase |

**Existence leak (non-interference):** dokumen yang tidak boleh dibaca
penanya (proyek restricted di luar `allowed_projects`, zona di luar
`allowed_zones`) dilewati sebelum penilaian dan tidak ikut menghitung idf.
Bagi penanya itu, keluaran apa pun sama persis dengan keluaran saat dokumen
tersebut tidak ada; tidak ada status khusus untuk topik restricted. Diuji
dengan menjalankan pertanyaan yang sama terhadap KB lengkap dan KB yang
dipangkas (`NonInterferenceTest`). Keputusan: [decisions/0002](decisions/0002-existence-leak-differential.md).

**Identitas di API** hanya dari field `user` yang persis cocok dengan nama di
`permissions.csv`; klaim di teks pertanyaan dan field `role` tidak dipakai.
Belum ada autentikasi: pemilih persona di UI berperan sebagai login demo.

**Wajib disaring di API (jangan pernah dikirim ke frontend):**

- `kb_root` — path server.
- `permission_gate` (termasuk `readable_ids` dan `dropped` untuk `risk_gate: enforce`).
- `quarantined` (isi), `mask_log`, `injection_check`.
- `permissions.allowed_projects` — bisa membocorkan nama proyek restricted.

## 5. Struktur repo & kepemilikan

```mermaid
flowchart LR
    R[tencent-hackathon/] --> KBD[knowledge-base/<br/>source/ · kb/]
    R --> BED[backend/<br/>scripts/ · tests/ · config.json]
    R --> FED[frontend/]
    R --> SKD[skill/<br/>SKILL.md · references/]
    R --> DOC[docs/]
    R --> TL[tools/pack_skill.py]
    TL -. rakit .-> DIST[dist/security-sahabat.skill]
    SKD & BED & KBD -. sumber .-> TL
```

| Folder | Isi | Owner |
| --- | --- | --- |
| `knowledge-base/` | Dokumen compliance + `permissions.csv` | Tim (perubahan via PR) |
| `backend/` | Retrieval, guard, permission gate, API | Izzat |
| `frontend/` | Chat UI | Rekan FE |
| `skill/` | Instruksi Claude Skill | Izzat |
| `docs/` | Desain sistem (file ini), `specs/` per fase, memory WorkBuddy | Semua |
| `adjusted_brief.md` | Brief proyek: rumusan masalah, S1–S6, 20 test case | Izzat |

## 6. Keputusan desain yang mengikat

1. **Tanpa kutipan = tanpa klaim.** Jawaban tanpa bukti di KB adalah "tidak tahu".
2. **Restricted = tidak ada.** Tidak dikonfirmasi maupun disangkal, termasuk di UI, log, dan pesan error.
3. **Kutipan verbatim** — PII hanya disamarkan di pertanyaan, tidak di kutipan.
4. **Ragu → tidak boleh**, lalu eskalasi ke owner dokumen.
5. Regresi `backend/tests/verify_matrix.py` (46 kasus) wajib lulus sebelum merge.

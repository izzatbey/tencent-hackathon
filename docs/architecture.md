# SecuritySahabat — System Design

Acuan bersama tim. Diagram di bawah memakai Mermaid (ter-render otomatis di GitHub).

Legenda status: **✅ sudah ada** · **🟡 direncanakan** (belum ada kodenya).

## 1. Gambaran sistem

```mermaid
flowchart LR
    U([Karyawan])

    subgraph FE["frontend/ — 🟡 Rekan (Frontend)"]
        UI[Chat UI<br/>pertanyaan + identitas]
        RV[Render jawaban<br/>kutipan, flag, eskalasi]
    end

    subgraph BE["backend/ — Izzat (Backend & Sistem)"]
        API["🟡 HTTP API<br/>POST /api/ask"]
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
    ID --> S[4. Retrieval KB<br/>istilah restricted disembunyikan dari query]
    S --> G[Permission gate<br/>buang dokumen di luar zona · flag risiko]
    G --> I2{5. Injection guard<br/>scope=evidence}
    I2 -- BLOCK --> QR[QUARANTINED<br/>dikeluarkan dari hits]
    I2 -- lolos --> C[6. Deteksi konflik<br/>CONFLICT · SUPERSEDED · REVIEW · RISK]
    QR --> C
    C --> D{Status}
    D -- restricted cocok --> R2[/"RESTRICTED_SILENCED · rc 2<br/>anggap tidak ada"/]
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

Response (hanya field ini yang boleh keluar ke browser):

```json
{
  "status": "OK",
  "rc": 0,
  "answer": "Tidak boleh. ...",
  "citations": [
    { "doc_id": "CTRL-09", "title": "A.8.20 Networks security",
      "section": "SSH exposure", "quote": "SSH (port 22) from the internet ...",
      "owner": "Citra Kusuma (SOC Analyst)" }
  ],
  "flags": [ { "type": "CONFLICT", "detail": "..." } ],
  "identity": { "user": "Andini Pratama", "role": "IT Admin" },
  "pii_masked": "NIK x1",
  "escalation": "Andini Pratama (IT Admin)"
}
```

| `status` | `rc` | Yang ditampilkan frontend |
| --- | --- | --- |
| `OK` | 0 | jawaban + daftar kutipan + flag (badge) |
| `NO_MATCH` | 3 | "Tidak tahu" (Template 3) + nama SME |
| `INJECTION_DETECTED` | 4 | permintaan parafrase |

**Existence leak:** API wajib mengirim `RESTRICTED_SILENCED` (rc 2) ke frontend
sebagai `NO_MATCH` dengan payload yang identik — status `RESTRICTED_SILENCED`
tidak boleh pernah sampai ke browser, karena status yang berbeda saja sudah
membedakan "dirahasiakan" dari "tidak ada". Proyek restricted terbuka hanya
bagi user yang `allowed_projects`-nya memuat `project` dokumen itu.

| Status internal | Status ke frontend |
| --- | --- |
| `OK` | `OK` |
| `RESTRICTED_SILENCED` | `NO_MATCH` |
| `NO_MATCH` | `NO_MATCH` |
| `INJECTION_DETECTED` | `INJECTION_DETECTED` |

**Wajib disaring di API (jangan pernah dikirim ke frontend):**

- `kb_root` — path server.
- `permission_gate.dropped` — berisi `doc_id` dokumen di luar akses penanya.
- `quarantined` (isi), `restricted_matches`, `mask_log`, `injection_check`.
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
5. Regresi `backend/tests/verify_matrix.py` (44 kasus) wajib lulus sebelum merge.

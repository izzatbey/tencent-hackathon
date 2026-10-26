# Phase 1 Build Instructions — WorkBuddy Agent Setup

> **Goal:** Build a basic Q&A agent that retrieves from 3 KBs and answers with inline citations.
> **Test:** Q-001 (port 22 → HR DB) and Q-004 (tunjangan makan — not in KB)

---

## Step 1: Create Knowledge Bases in WorkBuddy

1. Open WorkBuddy in your browser
2. Go to **Knowledge Base** section
3. Create 3 new knowledge bases:

### KB1: "NLP Compliance Controls"
- Upload `controls.md` as the source document
- Chunking: Use paragraph-level chunking (each control is a separate paragraph)
- Verify that chunks contain stable IDs like `[CTRL-01]`, `[CTRL-02]`, etc.

### KB2: "NLP SOPs & Policies"
- Upload `sops.md` as the source document
- Chunking: Use section-level chunking (each SOP is a separate section)
- Verify that SOP-7, SOP-9, SOP-12, SOP-14, SOP-15 are separate chunks

### KB3: "NLP Network Topology"
- Upload `topology.md` as the source document
- Chunking: Use section-level chunking
- Verify that network segments, maintenance windows, and asset dependencies are separate chunks

---

## Step 2: Create the Agent

1. Go to **Agent Builder** in WorkBuddy
2. Create a new agent named **"SecuritySahabat"**
3. In the **System Prompt** field, paste the entire content of `system_prompt_mvp.md`

---

## Step 3: Configure Retrieval

1. Add a **Retrieval** node to the workflow
2. Configure it to search ALL 3 knowledge bases simultaneously:
   - KB1: "NLP Compliance Controls"
   - KB2: "NLP SOPs & Policies"
   - KB3: "NLP Network Topology"
3. Set retrieval parameters:
   - Top-K: 8 chunks per KB (total 24 chunks max)
   - Relevance threshold: 0.5 (adjust if needed)
   - Include metadata: document name, section title

---

## Step 4: Configure Answer Synthesis

1. Add an **LLM** node after retrieval
2. Set the model to your preferred model (e.g., GPT-4o, Claude, or WorkBuddy's default)
3. The system prompt (from Step 2) will handle the synthesis logic
4. Configure the node to:
   - Receive: user question + retrieved chunks
   - Output: formatted answer with inline citations

---

## Step 5: Test the Agent

### Test 1: Q-001 (High-risk question)

**Input:**
```
Pak, mau tanya, kalau kita mau buka port 22 dari internet ke db-hr-jkt-01 untuk maintenance malam ini, itu boleh gak sesuai policy kantor? Risk-nya gimana?
```

**Expected output:**
- Direct answer: "Tidak boleh" — CRITICAL risk
- Citations: [CTRL-09], [CTRL-10], [topology.md: HR Database Segregation]
- Risk explanation: data breach, NIK exposure, PP 33/2026 violation
- Next steps: use jump-host + MFA, submit CAB request, contact Andini

**Pass criteria:**
- [ ] Says "tidak boleh" or equivalent
- [ ] Cites at least CTRL-09 (A.8.20 Networks security)
- [ ] Cites topology.md (HR DB segregated VLAN)
- [ ] Explains risk (data breach, NIK)
- [ ] Names SME/contact (Andini Pratama)

### Test 2: Q-004 ("I don't know")

**Input:**
```
halo, saya staff baru di gudang Makassar. Tanya: tunjangan makan bulanan berapa sekarang?
```

**Expected output:**
- "I don't know" or equivalent
- No invented numbers
- Directs to appropriate SME (HR/Finance)

**Pass criteria:**
- [ ] Does NOT invent a number for tunjangan makan
- [ ] Says "tidak menemukan informasi" or equivalent
- [ ] Names SME owner (Indah Permatasari or Dewi Anggraini)

---

## Step 6: Document Results

For each test, take a screenshot of:
1. The input question
2. The agent's answer (full text)
3. The retrieved chunks (if visible in WorkBuddy UI)

Save screenshots to `test_results/` folder for later submission.

---

## Troubleshooting

### Issue: Agent doesn't cite sources
**Fix:** Check that retrieval is returning chunks. If chunks are empty, adjust the retrieval query or lower the relevance threshold.

### Issue: Agent invents control IDs
**Fix:** Add explicit instruction in system prompt: "Never invent control IDs. Only cite IDs present in the retrieved evidence."

### Issue: Agent answers in English when question is in Indonesian
**Fix:** Add explicit instruction: "Answer in the same language as the user's question."

### Issue: Retrieval returns irrelevant chunks
**Fix:** Adjust chunking strategy (smaller chunks) or increase relevance threshold.

---

## Next Steps (Phase 2+)

After Phase 1 MVP works:
- **Phase 2:** Add permission gate (filter KBs by user persona before retrieval)
- **Phase 3:** Add conflict flagging (when SOP-7 vs October memo both retrieved)
- **Phase 4:** Add injection detection + PII masking
- **Phase 5:** Add approval gate + audit log

---

*End of Phase 1 build instructions.*

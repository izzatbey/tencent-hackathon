# Project Memory — Tencent Cloud Hackathon Indonesia 2026

## Key Facts
- **Hackathon:** Tencent Cloud Hackathon Indonesia 2026 ("AI CAN DO IT")
- **Challenge:** Challenge A — The Workplace Brain
- **Deadline:** 1 November 2026 (submission), 27 November 2026 (Demo Day)
- **Platform:** Tencent Cloud WorkBuddy (no deep coding, agent orchestration)
- **Team:** Solo (user: Muhammad Izzat)
- **Problem statement:** Security awareness gap — employees don't know what's allowed/not allowed from compliance perspective. Answers scattered across SOPs, chat, senior staff memory.
- **Solution:** Permission-aware Q&A agent that answers "boleh atau tidak?" with citations, conflict flagging, and audit trail.

## Architecture (Adjusted)
- 5 stages: Intake/Parser (LLM) → Permission Gate (code) → RAG (2 KBs parallel) → Answer Synthesizer (LLM) → Approval Gate (conditional) + Audit Log
- NO external decision service (removed Jev/Laya dependency)
- NO consensus engine (removed JSD math)
- Mock data: PT Nusantara Logistik Prima (NLP) — fictional logistics company

## Submission Requirements
1. Project title + blurb (under 10 words)
2. Project description (overview, insight, solution design, business value)
3. Accountability sheet (1 page)
4. Test results (~20 cases, screenshots, include failures)
5. Architecture diagram
6. Demo video (5-8 min, must show refuse/clarify/await-approval)
7. Product sharing (WorkBuddy value)
8. Source code (exported WorkBuddy workflow + mock data repo)

## Judging (10 dimensions × 10 points = 100)
Impact, Human-Centered Design, AI Interaction, Technical Execution, Feasibility, Demo & Storytelling, Innovation, UX & Accessibility, Responsible AI & Ethics, Overall Quality

## Critical Rules
- 5 accountability rules: show sources, stay in permissions, ask before acting, admit limits, keep record
- Critical failures cap Responsible AI score at 5/10
- Concealing failures penalized more than failures themselves
- Live surprise test: 90 seconds on Demo Day

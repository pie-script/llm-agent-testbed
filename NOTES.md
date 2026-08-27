# 📓 Project Notes: LLM Agent Security Testbed

## 🎯 Overview
An empirical testing harness designed to evaluate how tool-equipped LLM agents respond to adversarial prompts across two contrasting backend paradigms:
1. **Naive Backend (`tools_naive.py`)**: Zero authorization or parameter validation (confused-deputy baseline).
2. **Hardened Backend (`tools_hardened.py`)**: Strict boundary validation, access control enforcement, and credential redaction.

---

## 📑 Documentation Index

| Document | Description |
|---|---|
| 📖 **[README.md](README.md)** | Main project architecture, attack taxonomy, and quickstart guide. |
| 📊 **[V1-RESULTS.md](V1-RESULTS.md)** | Detailed walk-through of all 5 attack runs, diagrams, and security takeaways. |
| 🔬 **[PHASE-6-REPORT.md](PHASE-6-REPORT.md)** | Technical report covering test harness validation, API quotas, and non-determinism analysis. |
| 📓 **[BUILD-JOURNAL.md](BUILD-JOURNAL.md)** | Full engineering log documenting daily design choices and implementation milestones. |

---

## 📈 Phase Execution Checklist

- [x] **Phase 0: Tool Loop Verification** — Validated function-calling loop with `gemini-3.6-flash` via `google-genai`.
- [x] **Phase 1: Scope & Threat Model** — Defined ground-truth secret (`s3cr3t-fake-admin-pw`), mock database, and tool-output inspection grading.
- [x] **Phase 2: Data Models** — Implemented immutable dataclasses (`FakeUser`, `FakeApiKey`, `AttackAttempt`, `AttackResult`).
- [x] **Phase 3: Tool Implementation** — Built `naive_get_user` (unfiltered) and `hardened_get_user` (access-controlled).
- [x] **Phase 4: Agent Tool Wiring** — Confirmed live Gemini agent execution against both tool versions standalone.
- [x] **Phase 5: Attack Suite** — Created test cases across 5 OWASP-aligned categories with planted indirect injection vectors.
- [x] **Phase 6: Multi-Turn Harness & Batch Runs** — Upgraded `runner.py` for multi-turn conversations and executed all 5 attack scenarios.
- [x] **Phase 7: Result Analysis & Spot-Checking** — Classified outcomes (`leaked`, `blocked`, `unclear`) and evaluated model judgment vs. tool defenses.
- [x] **Phase 8: Reporting & Visual Assets** — Generated complete documentation, summary tables, and visual SVG/PNG diagrams.

---

## 💡 Key Architectural Takeaways

1. **The Vulnerability Lives in Application Code**:  
   The LLM is simply a natural-language router. If the backend function executes requests without validating permissions, the system is vulnerable regardless of model safety training.
2. **Vocabulary Evasion**:  
   Blunt prompts mentioning `"password"` or `"credentials"` were consistently caught by the model's safety filters. However, mundane engineering requests (*"show all fields for an export schema"*) bypassed model filters and fully exploited the naive tool.
3. **Defense in Depth**:  
   Hardening must be enforced at the Python/tool boundary. The hardened tool resisted all direct and boundary bypass attacks because it refuses restricted records before any data is returned.

---

## 🔮 Future Roadmap (v2)

- [ ] Multi-sample repeat testing per attack to calculate probabilistic leak rates (e.g. $N=5$ runs per attack).
- [ ] Containerized sandbox execution environment.
- [ ] Extended multi-turn social engineering trees.
- [ ] Automated CI evaluation pipeline.

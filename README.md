# ConsiliumMD: The Majestic Clinical Frontend for CARMA

<div align="center">
  <img src="https://img.shields.io/badge/Status-Development-blue" alt="Status" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi" alt="Backend" />
  <img src="https://img.shields.io/badge/Frontend-React%2018-61DAFB?logo=react" alt="Frontend" />
  <img src="https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql" alt="Database" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License" />
</div>

<br/>

**ConsiliumMD** is a production-ready, highly secure web portal serving as the clinical operating system for **CARMA** (Conflict-Aware Reasoning with Mathematical Assurance). 

Traditional medical AIs act as "black box oracles" that hallucinate when medical guidelines conflict. ConsiliumMD brings the mathematical rigor of Inverse Decision Theory (CARMA) to the bedside through a frictionless, majestic user experience.

---

## 🌟 The Vision
ConsiliumMD is designed to be the ultimate **Zero-Friction Clinical UX**. It translates complex mathematical uncertainty into intuitive, beautiful dashboards that doctors actually want to use.

### Elite Architecture
*   **Cinematic Patient Data Canvas**: Real-time rendering of multimodal patient data (X-Rays, DICOM volumes, NLP-extracted prescriptions, and IoMT telemetry).
*   **The 5-State Routing UI**: Maps mathematical bounds directly to clinician workflow:
    1.  **Answer:** Consensus reached. Standard recommendation card.
    2.  **Retrieve:** Epistemic conflict (missing data). Drag-and-drop file uploader triggered.
    3.  **Elicit:** Normative conflict (value mismatch). Generative Elicitation Scale triggered to ask for patient preferences.
    4.  **Warn:** High Reversal Risk. Mandatory acknowledgment required.
    5.  **Escalate:** Mathematical collapse. Routed to Senior Clinician queue.
*   **Strict RBAC (Role-Based Access Control)**: Segmented dashboards for Doctors, Senior Clinicians, and Compliance Admins.
*   **Zero-Hallucination Guardrails**: Pharmacogenomic deterministic checking via RxNorm/SIDER before any prescription recommendation is finalized.

---

## 📚 Documentation
The absolute source of truth for the architecture, UI definitions, and phase planning is the master implementation document:
*   📖 [**ConsiliumMD Full Implementation Plan**](./ConsiliumMD_implementation_plan.md)

---

## 🚀 Getting Started (Clean Slate)

This repository has been wiped clean of legacy prototype code to prepare for the rigorous Phase 1 implementation detailed in the master plan.

### Upcoming Tech Stack
*   **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, WebGL (for DICOM viewing).
*   **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL.
*   **Auth**: JWT (Access/Refresh), bcrypt.

### Next Steps
1. Initialize the monolithic backend/frontend structure.
2. Build the strict RBAC models and FastAPI JWT middleware.
3. Scaffold the Cinematic Patient Canvas in React.

*(Development commands will be populated here as Phase 1 commences.)*

---

## 🔒 Compliance & Data Privacy
ConsiliumMD is architected for strict HIPAA/GDPR compliance:
*   **Pre-LLM Scrubbing**: NLP tokenization (Microsoft Presidio) strips all Protected Health Information (PHI) before it ever touches an LLM.
*   **Encryption**: AES-256 (At Rest) and TLS 1.3 (In Transit).
*   **Audit**: 100% immutable, append-only DB triggers for all data access events.

---

## 🎓 Academic Strategy
This repository is part of a "Two-Paper" publication strategy targeting top-tier medical informatics journals (*npj Digital Medicine*, *JAMIA*) and A* CS conferences (*NeurIPS*). Please refer to the `CITATION.cff` for attribution guidelines.

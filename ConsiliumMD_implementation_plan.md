# ConsiliumMD: Full Implementation Plan

## 1. Project Overview
ConsiliumMD is a majestic, production-ready web portal with Role-Based Access Control (RBAC) that serves as the clinical frontend for **CARMA** (Conflict-Aware Reasoning with Mathematical Assurance). It seamlessly integrates medical image processing and document extraction pipelines to allow medical professionals to retrieve data directly from patient uploads (X-rays, MRIs, PDFs, prescriptions), leveraging CARMA as the central decision engine.

## 2. Core Features
- **Majestic Web Portal with RBAC**: A visually stunning, highly responsive, and premium frontend built with modern design principles (React, Tailwind CSS, micro-animations). 
- **Multimodal Data Retrieval & Processing**: Medical professionals can directly upload and extract insights from Medical Images and Documents.
- **CARMA as the Decision Engine**: Direct integration with the CARMA reasoning engine for conflict-aware clinical decision support, displaying evidence-derived confidence and resolving evidence gaps vs. judgment calls through a **2D Confidence Space** combining RPD (Revealed-Preference Decomposition) and Longitudinal Reversal Risk prediction.
- **Flawless Execution**: High availability, comprehensive test coverage, robust error handling, and append-only audit logging for compliance.

## 3. Architecture & Pipelines

### 3.1 Web Portal, RBAC & Premium UI
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS. Features dynamic, visually rich dashboards strictly tailored to user roles.
- **Cinematic Patient Data Canvas**: A majestic, glassmorphic dashboard that beautifully renders all ingested multimodal patient data. Lab results are rendered as dynamic sparklines, OCR'ed prescriptions as structured medication cards, and vitals feature subtle micro-animations (e.g., a pulsing heart rate indicator).
- **Advanced Visualizations**:
  - **Dynamic Argument Flow**: An animated directed graph visualizing the CARMA adversarial debate.
  - **Generative Elicitation Scale**: A glowing balance scale that dynamically tilts as clinicians input values (e.g., "Longevity" vs. "Quality of Life") during an `Elicit` state.
  - **3D Interactive Patient Digital Twin**: An immersive 3D human body mesh where relevant organs illuminate with condition tags.
  - **"What-If" Counterfactual Simulation**: A dynamic slider board to tweak patient variables and watch the 2D Confidence Space shift in real-time.
- **Ambient Clinical Dictation**: Integration of `Whisper.cpp` allowing doctors to dictate patient context with their voice for zero-friction data entry.
- **Smart Clinical Input & Epistemic Resolution**: A dual-input interface for ad-hoc queries. When CARMA triggers a `Retrieve` state (Epistemic Gap), doctors can either directly type the missing value or drag-and-drop a lab PDF to resolve it.
- **The RBAC Matrix**:
  - **Doctor / Clinician**: The primary user. Uploads data, receives recommendations, resolves `Elicit` states.
  - **Senior Clinician / Reviewer**: The human backstop for `Escalate` states.
  - **Admin / Compliance Officer**: Manages roles, monitors the "Institutional Reversal Radar", and reads the append-only `audit_events` log.

### 3.2 Multimodal Ingestion (Images & PDFs)
- **Image Pipeline**: Secure DICOM/Image upload. Vision models (MedSAM, ViT) analyze X-rays, MRIs, and CT scans.
- **Interactive WebGL DICOM Viewer with AI Overlays**: Embeds an open-source DICOM viewer in the browser where the AI draws bounding boxes over anomalies, and hovering highlights the specific CARMA evidence.
- **Document Pipeline**: OCR and NLP extraction of key entities from clinical notes and prescriptions.
- **Multimodal Discrepancy Detection**: ConsiliumMD cross-references the output of its own pipelines (e.g., OCR text vs. Vision Model output) and halts/escalates if they contradict.

### 3.3 IoMT & Real-Time Hardware Telemetry Pipeline (Phase 4)
- **Ingestion (Academic Simulation)**: For MVP and academic demonstration, connecting to proprietary hospital hardware is unfeasible. Instead, we implement a `mock_vitals_streamer.py` that reads historical high-frequency telemetry from the **MIMIC-IV** dataset and streams it over WebSockets, flawlessly simulating live ICU monitor data (Heart Rate, SpO2).
- **Processing**: A time-series database (e.g., InfluxDB) buffers telemetry. An edge-detection algorithm watches for critical threshold breaches.
- **Output**: Automatic, zero-click triggering of the CARMA engine when real-time simulated hardware data diverges from the predicted clinical path.

### 3.4 CARMA Decision Engine Integration & UI State Mapping
ConsiliumMD maps CARMA's mathematical outputs to its **5-State Routing UI**:
- **Epistemic Conflict (Missing State $S$):** Triggers the **`Retrieve` State**.
- **Normative Conflict (RPD Weight Divergence $\Delta w$):** Triggers the **`Elicit` State**.
- **Longitudinal Reversal Risk (Hazard > Threshold):** Triggers the **`Warn` State**.
- **ECL Collapse / Unsafe Bounds:** Triggers the **`Escalate` State**.
- **Consensus:** Triggers the **`Answer` State** with a standard recommendation card.
- **Data Completeness Gatekeeper**: An algorithmic triage layer that calculates "Contextual Entropy" before querying the LLM, refusing queries missing critical variables.
- **Pharmacogenomic & Polypharmacy Guardrails**: A deterministic rule engine (RxNorm/SIDER) guarantees drug dosages do not conflict with the patient's existing profile.
- **Continuous Reversal Surveillance**: A background daemon monitors newly published guidelines. If the Reversal Risk engine flags a previously sound protocol, it triggers a retrospective "Fragility Alert".
- **Federated Preference Learning (Normative Memory)**: The system learns institutional baselines (e.g., "Cardiology favors Quality of Life") to smartly pre-suggest preferences in future `Elicit` states.

### 3.5 Workflow Acceleration (Zero-Friction Clinician UX)
- **Auto-Drafted SOAP Notes**: ConsiliumMD auto-generates perfectly formatted SOAP notes containing the clinical rationale.
- **1-Click EHR Export (SMART on FHIR)**: Pushes CARMA recommendations and SOAP notes directly into Epic or Cerner.
- **Automated Pre-Rounding Summaries (Morning Huddle)**: A background worker pre-flags patients on high-risk protocols on a dashboard at 7:00 AM.
- **Auto-Generated ICD-10 & CPT Billing Codes**: Automatically suggests diagnostic and procedure codes based on accepted interventions.

### 3.6 Comprehensive Patient Data Management Workflow
ConsiliumMD serves as a robust, longitudinal patient registry:
- **Patient Profile Creation & Storage**: Persistent storage in PostgreSQL serving as the baseline `PatientContext`.
- **Longitudinal Case History**: Chronological timeline of every past CARMA recommendation, extracted evidence, and clinical action.
- **Dynamic Context Updating**: Automatic updating of the patient profile as new multimodal data is ingested.

### 3.7 Data Privacy & HIPAA/GDPR Compliance Pipeline
- **Pre-LLM PHI Scrubbing (Anonymization Gateway)**: NLP scrubbing (e.g., Microsoft Presidio) replaces PHI with generic tokens. The LLM never sees identifying data.
- **Encryption**: AES-256 at rest, TLS 1.3 in transit.
- **Immutable Auditing**: Every data access event is permanently recorded in the append-only `audit_events` table.

### 3.8 VRAM Orchestration (Consumer Hardware Constraint)
To run locally on consumer hardware (e.g., RTX 3060 6GB VRAM):
- The backend dynamically unloads multimodal Vision/OCR models from VRAM after parsing uploads.
- It then allocates VRAM to load the CARMA LLM (e.g., Llama-3-8B-Instruct quantized) to execute the RPD debate, preventing OOM crashes.

## 4. Phased Implementation Strategy

### Phase 1: Majestic Web Portal Foundation & Patient Management
- Set up the React frontend with the premium Cinematic Patient Data Canvas and glassmorphic UI.
- Implement Auth, the strict RBAC matrix, and Patient Data Management workflows.

### Phase 2: Multimodal Pipelines & Workflow Acceleration
- Build PDF parsing, OCR, and the Interactive WebGL DICOM Viewer.
- Integrate 1-Click EHR Export, SOAP note drafting, and Billing Code generation.

### Phase 3: CARMA Integration & Advanced Visualizations
- Connect the backend to the CARMA engine. Map mathematical outputs to the 5-State Routing UI.
- Implement the "What-If" Counterfactual Simulation, Dynamic Argument Flow, and Generative Elicitation Scale.
- Deploy the VRAM Orchestration architecture.

### Phase 4: IoMT Simulation & Advanced Guardrails
- Implement the `mock_vitals_streamer.py` for IoMT simulation.
- Deploy the Pharmacogenomic Guardrails, Continuous Reversal Surveillance, and Pre-LLM PHI Scrubbing.

## 5. Real Data Gathering & Demonstration Plan
- **MIMIC-IV / MIMIC-IV-Note**: For patient profiles, clinical notes, and IoMT simulation data.
- **MIMIC-CXR & CheXpert**: For testing the DICOM Viewer and Vision pipelines.
- **CECB-T**: To test the RPD and Reversal Risk engines.

## 6. Automated Test Suite Plan
- **Backend**: `pytest` for all endpoints, DB integrity, and multimodal pipeline verification.
- **Frontend**: Vitest/React Testing Library for UI components; Playwright for E2E workflows (Upload -> Extract -> CARMA -> Recommendation).

## 7. Publication Strategy & Open-Source Readiness
Supports the "Two-Paper" publication strategy (Targeting *npj Digital Medicine*, *JAMIA*, *NeurIPS*).
- **1-Click Reproducibility**: `docker-compose` orchestration.
- **Citation**: `CITATION.cff` file.
- **Data Compliance**: De-identified datasets and fixtures.

## 8. Clinical Validation & Academic Evaluation Methodology
- **Retrospective Cohort**: $N=1,000$ MIMIC-IV cases.
- **Primary Endpoints**: Routing Accuracy ($F_1$-score) and Discrepancy Detection Rate.
- **Clinical Utility**: Time-to-Decision ($\Delta t$) and System Usability Scale (SUS).
- **Safety**: Bounded $0\%$ critical failure rate for Pharmacogenomic Guardrails; evaluation of Guideline Drift Sensitivity.

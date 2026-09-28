# ConsiliumMD: Full Implementation Plan

## 1. Project Overview
ConsiliumMD is a majestic, production-ready web portal with Role-Based Access Control (RBAC) that serves as the clinical frontend for **CARMA** (Conflict-Aware Reasoning with Mathematical Assurance). It seamlessly integrates medical image processing and document extraction pipelines to allow medical professionals to retrieve data directly from patient uploads (X-rays, MRIs, CT scans, PDFs, prescriptions), leveraging CARMA as the central decision engine.

## 2. Core Features
- **Majestic Web Portal with RBAC**: A visually stunning, highly responsive, and premium frontend built with modern design principles (React, Tailwind CSS, micro-animations). Roles include Admin, Doctor, Reviewer/Senior Clinician, and Nurse.
- **Multimodal Data Retrieval & Processing**: Medical professionals can directly upload and extract insights from:
  - **Medical Images**: X-rays, MRIs, and CT scans (Medical Image Processing Pipeline).
  - **Documents**: Medical reports, prescriptions, and clinical notes (PDF to Text / OCR Pipeline).
- **CARMA as the Decision Engine**: Direct integration with the CARMA reasoning engine for conflict-aware clinical decision support, displaying evidence-derived confidence and resolving evidence gaps vs. judgment calls through a **2D Confidence Space** combining RPD (Revealed-Preference Decomposition) and Longitudinal Reversal Risk prediction.
- **Flawless Execution**: High availability, comprehensive test coverage, robust error handling, and append-only audit logging for compliance.

## 3. Architecture & Pipelines

### 3.1 Web Portal, RBAC & Majestic UI
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS. Features dynamic, visually rich dashboards strictly tailored to user roles.
- **Cinematic Patient Data Canvas**: A majestic, glassmorphic dashboard that beautifully renders all ingested multimodal patient data. Instead of raw text blocks, lab results are rendered as dynamic sparklines, OCR'ed prescriptions as structured medication cards, and vitals with subtle micro-animations (e.g., a pulsing heart rate indicator), ensuring total situational awareness for the clinician at a glance.
- **3D Interactive Patient Digital Twin**: An immersive 3D human body mesh. As multimodal data is ingested (e.g., chest X-rays, renal lab tests), the relevant organs illuminate with condition tags. Clinicians can rotate the model and click on an organ to instantly filter all extracted CARMA evidence for that specific physiological system.
- **Dynamic Argument Flow (Animated Network Graph)**: A stunning, animated directed graph to visualize the CARMA adversarial debate. Nodes represent specific guidelines (e.g., AHA, NICE), and pulsing edges (red for conflict, green for concordance) visually funnel into the final recommendation.
- **Generative Elicitation Scale**: When the system triggers an `Elicit` state (Judgment Call), it renders a glowing, glassmorphic balance scale. As the clinician adjusts their value preference (e.g., "Longevity" vs. "Quality of Life"), the scale visually tilts and the recommendation text dynamically rewrites itself.
- **2D Confidence Space Scatterplot**: A dynamic 3D or 2D scatterplot mapping the current case against historical reversals (Reversal Risk on X-axis, RPD severity on Y-axis).
- **Evidence Topography Heatmap**: A visual map showing clusters of evidence, visually differentiating epistemic gaps from normative camps, giving clinicians an intuitive view of medical consensus.
- **"What-If" Counterfactual Simulation**: A dynamic slider board where a clinician can instantly tweak patient variables (e.g., changing age or eGFR) and watch the 2D Confidence Space (RPD & Reversal Risk) shift in real-time.
- **Cinematic Reasoning Replay**: A "play" button that visually steps through CARMA's decision-making process in a 10-second animated sequence—from raw DICOM extraction to plotting on the 2D Confidence Space, to resolving the adversarial debate, ensuring total, intuitive transparency.
- **Ambient Clinical Dictation**: Integrate `Whisper.cpp` in the browser so doctors can dictate patient context with their voice for zero cost, bypassing typing entirely.
- **Smart Clinical Input & Epistemic Resolution Forms**: A sleek, predictive dual-input interface for ad-hoc queries and gap resolution. When CARMA triggers a `Retrieve` state (Epistemic Gap), the UI dynamically generates a beautiful prompt (e.g., "Missing Patient's LDL Cholesterol"). The doctor has complete flexibility: they can either **directly type** the missing value into a glowing input field, OR **drag-and-drop** the missing lab PDF/DICOM file for automatic extraction. Both paths seamlessly unblock the CARMA engine.
- **Backend & Auth**: FastAPI handles JWT-based Auth (Access/Refresh tokens) and enforces a strict permission matrix.
- **The RBAC Matrix**:
  - **Doctor / Clinician**: The primary user. Can upload multimodal data, receive CARMA recommendations, acknowledge `Warn` states, resolve `Elicit` states, and override decisions.
  - **Senior Clinician / Reviewer**: The human backstop. Their dashboard exclusively receives cases where CARMA triggers the `Escalate` state (e.g., non-identifiable conflicts, ECL graph collapse). They provide final resolution.
  - **Admin / Compliance Officer**: Has zero clinical access. Their dashboard manages user roles, tracks the append-only `audit_events` log, and monitors the **Institutional Reversal Radar** (a radar chart showing hospital-wide guideline drift where current local protocols sit in the high-reversal-risk danger zone).
- **Database**: PostgreSQL for storing patient data, clinical cases, recommendations, and immutable audit logs.

### 3.2 Medical Image Processing Pipeline
- **Ingestion**: Secure DICOM and standard image upload endpoint.
- **Processing**: Vision models (e.g., MedSAM, specialized ViT models, or integrated external APIs) analyze X-rays, MRIs, and CT scans.
- **Interactive WebGL DICOM Viewer with AI Overlays**: Don't just extract text. Embed an open-source DICOM viewer in the browser where the AI draws bounding boxes over anomalies, and hovering over them highlights the specific CARMA evidence.
- **Output**: Extracted clinical findings and structured visual contexts are fed directly into the patient context for CARMA.

### 3.3 PDF & Document Retrieval Pipeline
- **Ingestion**: Secure PDF and image (prescription) upload.
- **Processing**:
  - OCR (Optical Character Recognition) via tools like Tesseract or cloud-based Document AI.
  - NLP extraction of key entities (medications, conditions, vitals, lab results).
- **Output**: Structured text appended to the patient's electronic health record and passed to CARMA for evidence grounding.

### 3.4 IoMT & Real-Time Hardware Telemetry Pipeline
- **Ingestion (Academic Simulation)**: For MVP and academic demonstration, connecting to proprietary hospital hardware is unfeasible. Instead, we implement a `mock_vitals_streamer.py` that reads historical high-frequency telemetry from the **MIMIC-IV** dataset and streams it over WebSockets, flawlessly simulating live ICU monitor data (Heart Rate, SpO2).
- **Processing**: A time-series database (e.g., InfluxDB) buffers the high-frequency telemetry. An edge-detection algorithm watches for critical threshold breaches (e.g., sudden SpO2 drop).
- **Output**: Live, pulsing vitals on the "Cinematic Patient Data Canvas" and automatic, zero-click triggering of the CARMA engine when real-time simulated hardware data diverges from the predicted clinical path.

### 3.5 CARMA Decision Engine Integration & UI State Mapping
ConsiliumMD acts as the orchestrator. Extracted multi-modal data is structured into a `ClinicalQuery` and sent to CARMA's API. ConsiliumMD strictly maps CARMA's mathematical outputs to its **5-State Routing UI**:
- **Epistemic Conflict (Missing State $S$):** If CARMA detects a missing factual premise, ConsiliumMD triggers the **`Retrieve` State**, actively prompting the clinician to upload the missing lab result or DICOM image.
- **Normative Conflict (RPD Weight Divergence $\Delta w$):** If CARMA's Inverse Optimizer detects divergent clinical values, ConsiliumMD triggers the **`Elicit` State**, rendering the "Generative Elicitation Scale" for the doctor to input patient preferences.
- **Longitudinal Reversal Risk (Hazard > Threshold):** If the Deep Survival model flags the guideline as fragile, ConsiliumMD triggers the **`Warn` State**, forcing a mandatory UI acknowledgment checkbox before the clinician can proceed.
- **ECL Collapse / Unsafe Bounds:** If the Evidential Conflict Landscape graph is completely disconnected, ConsiliumMD triggers the **`Escalate` State**, safely bypassing the AI and routing to a human senior reviewer.
- **Consensus:** Triggers the **`Answer` State** with a standard recommendation card.

#### Advanced Functional & Quality Improvements (Non-UI Backend Guardrails)
- **Continuous Reversal Surveillance (Background Daemon)**: The system longitudinally tracks accepted recommendations. A background worker continuously monitors newly published guidelines and medical literature. If the CARMA Reversal Risk engine detects that a previously sound protocol has suddenly become "high-risk," it triggers a retrospective "Fragility Alert" to the prescribing clinician.
- **Multimodal Discrepancy Detection**: ConsiliumMD cross-references the output of its own pipelines. If the OCR text from a radiologist's PDF report says "No signs of cardiomegaly," but the local Vision Model analyzing the raw DICOM X-ray flags an enlarged heart, the system halts and escalates a `Cross-Modality Discrepancy` alert before querying CARMA.
- **Pharmacogenomic & Polypharmacy Guardrails**: Enhance the post-synthesis Safety Auditor with a deterministic rule engine (referencing RxNorm/SIDER). Before CARMA's recommendation is finalized, it guarantees the suggested drug dosage does not conflict with the patient's existing polypharmacy profile or known genetic metabolizer status, ensuring a strict zero-hallucination guarantee for prescriptions.
- **Federated Preference Learning (Normative Memory)**: When the system resolves an `Elicit` (Judgment Call) state, it records the clinician's normative choice. Over time, ConsiliumMD learns the baseline preference of specific hospital departments (e.g., "Cardiology strongly favors Quality of Life for 80+ patients"). Future elicitations can smartly pre-suggest this institutional baseline, speeding up clinical workflows.
- **Data Completeness Gatekeeper (Pre-CARMA Triage)**: An algorithmic triage layer that calculates "Contextual Entropy" before ever querying the LLM. If critical variables required by standard guidelines are missing (e.g., trying to calculate ASCVD risk without an HDL cholesterol lab), it refuses the query and explicitly prompts the clinician to order the missing lab, saving compute costs and preventing "garbage-in, garbage-out."

### 3.6 Workflow Acceleration (Zero-Friction Clinician UX)
- **1-Click EHR Export (SMART on FHIR)**: Instead of copy-pasting, doctors can click "Export to EHR" to push the CARMA recommendation, evidence citations, and SOAP note directly into Epic or Cerner via HL7 FHIR standards.
- **Auto-Drafted SOAP Notes**: When a clinician resolves a case, ConsiliumMD auto-generates a perfectly formatted SOAP note containing the clinical rationale, ready for 1-click copy/paste into their EHR.
- **Automated Pre-Rounding Summaries (Morning Huddle)**: A background worker runs overnight on the doctor's patient census. When the doctor logs in at 7:00 AM, ConsiliumMD provides a "Morning Huddle" dashboard, pre-flagging any patients currently on protocols that have tripped a `Warn` (High Reversal Risk) alert before the doctor even opens a chart.
- **Auto-Generated ICD-10 & CPT Billing Codes**: When a doctor accepts a CARMA recommendation, the system automatically parses the intervention and suggests the most accurate, compliant ICD-10 diagnostic and CPT procedure codes, instantly saving administrative billing time.

### 3.7 Comprehensive Patient Data Management Workflow
ConsiliumMD is not just a stateless calculator; it serves as a robust, longitudinal patient registry for the clinician:
- **Patient Profile Creation & Storage**: Clinicians can create and save detailed patient profiles (demographics, chronic conditions, active medications, allergies). This data is persistently stored in PostgreSQL and serves as the baseline `PatientContext` for all future CARMA queries.
- **Longitudinal Case History**: When a doctor views a patient, they see a chronological timeline of every past CARMA recommendation, the extracted evidence that drove it, and the final clinical action taken.
- **Dynamic Context Updating**: As new multimodal data (PDFs/Images) or real-time IoMT telemetry is ingested, the patient's central profile is automatically updated. If a new lab result contradicts an old one, the system flags the updated state for the clinician's review.

### 3.8 Data Privacy & HIPAA/GDPR Compliance Pipeline
To ensure deployability in highly regulated clinical environments, ConsiliumMD enforces strict data boundaries:
- **Pre-LLM PHI Scrubbing (Anonymization Gateway)**: Before any patient context is sent to the CARMA engine, it passes through a local NLP scrubbing layer (e.g., Microsoft Presidio). All Protected Health Information (PHI) like names, SSNs, and birthdates are replaced with generic tokens (e.g., `[PATIENT_A]`, `[AGE_65]`). The LLM never sees identifying data.
- **Encryption**: The PostgreSQL database encrypts all records at rest (AES-256). All data in transit (REST/WebSockets) is secured via TLS 1.3.
- **Immutable Auditing**: Every data access event is permanently recorded in the append-only `audit_events` table, satisfying HIPAA access log requirements.

### 3.9 VRAM Orchestration (Consumer Hardware Constraint)
To ensure the system can run locally on consumer-grade hospital hardware (e.g., RTX 3060 6GB VRAM), ConsiliumMD implements a strict **Model-Swapping Architecture**:
- The backend dynamically unloads the multimodal Vision/OCR models from VRAM after parsing the uploaded images/PDFs.
- It then allocates the VRAM to load the CARMA LLM (e.g., Llama-3-8B-Instruct quantized) to execute the RPD debate, completely preventing Out-Of-Memory (OOM) fatal crashes.

## 4. Phased Implementation Strategy

### Phase 1: Majestic Web Portal Foundation & Patient Management
- Set up the React frontend with the premium Cinematic Patient Data Canvas and glassmorphic UI.
- Implement JWT-based Auth and the strict RBAC matrix (Admin, Doctor, Senior Clinician).
- Scaffold the patient dashboard, Patient Profile Creation, and case management views.

### Phase 2: Multimodal Ingestion Pipelines & Visualizations
- **Document Pipeline**: Build PDF parsing and OCR for prescriptions and clinical reports.
- **Image Pipeline**: Build the secure DICOM image upload component and the Interactive WebGL DICOM Viewer with AI Overlays.
- Implement the 3D Interactive Patient Digital Twin for visual filtering of evidence.

### Phase 3: CARMA Integration & Advanced UX
- Connect the backend to the CARMA reasoning engine (`/api/v1/analyze`) and deploy the Pre-CARMA Triage Gatekeeper.
- Map mathematical outputs to the 5-State Routing UI (Retrieve, Elicit, Warn, Escalate, Answer).
- Implement the Dynamic Argument Flow graph, Generative Elicitation Scale, and "What-If" Counterfactual Simulation.
- Integrate the Ambient Clinical Dictation via Whisper.cpp.

### Phase 4: Workflow Acceleration, Compliance & Simulation
- **Workflow Acceleration**: Integrate 1-Click EHR Export, Auto-Drafted SOAP Notes, and Morning Huddles.
- **IoMT**: Implement the `mock_vitals_streamer.py` for real-time hardware telemetry simulation.
- **Guardrails**: Deploy the Pharmacogenomic Guardrails, Continuous Reversal Surveillance, and Multimodal Discrepancy Detection.
- Finalize compliance requirements (PHI scrubbing, append-only audit logs) and VRAM orchestration.

## 5. Real Data Gathering & Demonstration Plan
To demonstrate the platform's power without relying on synthetic mocks, we will use robust, open-source real-world datasets:

### 5.1 Patient Profiles & Medical Notes
- **MIMIC-IV**: The gold standard for de-identified ICU and emergency patient data. We will extract realistic patient profiles (vitals, lab results, diagnoses).
- **MIMIC-IV-Note**: Real de-identified clinical notes, discharge summaries, and radiology reports to test the PDF/Document text-extraction and OCR pipelines in real clinical syntax.

### 5.2 Medical Imaging
- **MIMIC-CXR & CheXpert**: Massive open-source datasets of chest X-rays. These provide perfect test cases for the Interactive DICOM Viewer and AI Overlays (highlighting cardiomegaly, consolidation, etc.).
- **fastMRI**: Real MRI datasets from NYU/Facebook for testing the image processing pipeline against non-X-ray modalities.

### 5.3 Guidelines & Evidence Base
- **CECB-T (Type-Labeled Clinical Evidence Conflict Benchmark)**: We will ingest real medical guidelines (ACC/AHA, USPSTF, NICE) explicitly curated in CARMA's foundational plan to test the RPD and Reversal Risk engines.

## 6. Automated Test Suite Plan
To guarantee the system works flawlessly, we will implement a multi-layered automated test suite:

### 6.1 Backend & Database (FastAPI + pytest)
- **Unit Tests**: Full coverage for all endpoints using `pytest`. Mocking the CARMA backend response with `respx` or `responses` to verify proper HTTP handling.
- **Database & Audit Integrity**: Integration tests using a test SQLite/Postgres instance to ensure the `audit_events` table strictly enforces its append-only DB triggers (attempting to UPDATE/DELETE must raise exceptions).
- **Multimodal Pipeline Verification**: Dedicated fixtures (1 known DICOM file, 1 known PDF) passed through the image/document pipelines to assert deterministic NLP and OCR extraction accuracy.

### 6.2 Frontend & UI (React + Vitest/Playwright)
- **Component Tests (Vitest + React Testing Library)**: Assert that specific UI elements render correctly depending on the data. For example, verifying the Recommendation Card accurately switches badge colors and panels based on the 5-state Routing Decision (e.g., rendering the `WARN` alert box).
- **End-to-End (E2E) Workflows (Playwright)**: Browser-based tests simulating a complete clinical user journey:
  1. Login as `doctor`.
  2. Upload a test X-ray and PDF.
  3. Verify the extraction populates the UI.
  4. Use the "What-If" slider.
  5. Accept a recommendation and verify the SOAP note is generated.

## 7. Publication Strategy & Open-Source Readiness
This implementation directly supports the project's **"Two-Paper" publication strategy**, serving as the translational foundation for the second paper:

### 7.1 Paper 2: The Systems & Translational Paper
- **Target Venues (Q1 & A*):** *npj Digital Medicine*, *JAMIA*, *The Lancet Digital Health*, and A* conferences like *NeurIPS* (Datasets/Benchmarks) or *MLHC* (Machine Learning for Healthcare).
- **Focus:** Demonstrating an end-to-end multimodal clinical workflow. ConsiliumMD ingests real-world data (PDFs, X-rays), parses it into a structured `PatientContext`, and utilizes the CARMA engine to trigger appropriate clinical routing (Answer, Retrieve, Elicit, Warn, Escalate).
- **Novelty:** Solving the "last-mile" problem of AI hallucination via safe, evidence-grounded gating in a deployable, premium UI.

### 7.2 Repository Publication Readiness
To ensure the repository is ready for peer-review and public open-source release from Day 1:
- **Reproducibility (Docker):** Full `docker-compose` orchestration encompassing the frontend, backend, database, and CARMA integration for 1-click reviewer setup.
- **Citation Standards:** Inclusion of a `CITATION.cff` file ensuring correct academic attribution.
- **Documentation:** High-quality `README.md`, architecture diagrams, and fully commented codebase adhering to clinical software best practices.
- **Data Compliance:** All provided sample datasets, fixtures, and database seeds will be rigorously de-identified to comply with open-data and HIPAA/GDPR standards.

## 8. Clinical Validation & Academic Evaluation Methodology
To guarantee acceptance in Q1 medical journals and A* computer science conferences, the system will undergo rigorous, statistically sound evaluation:

### 8.1 Retrospective Cohort Evaluation (Quantitative)
- **Dataset:** A stratified sample of $N=1,000$ complex patient cases extracted from MIMIC-IV, ensuring representation across highly debated clinical topics (e.g., lipid management in the elderly).
- **Primary Endpoints:** 
  - **Routing Accuracy:** Precision, Recall, and $F_1$-score of the system correctly mapping cases to the 5-state UI (Answer, Retrieve, Elicit, Warn, Escalate) compared against a gold-standard board of 3 senior clinicians.
  - **Discrepancy Detection Rate:** Measuring the True Positive Rate (TPR) of the Multimodal Discrepancy Detection engine when fed deliberately contradictory image-text pairs.

### 8.2 Clinical Utility & Workflow Metrics (Qualitative & Operational)
- **Time-to-Decision ($\Delta t$):** Measuring the reduction in time required for a clinician to reach a final, evidence-backed decision using ConsiliumMD vs. a standard EHR + manual UpToDate search baseline.
- **System Usability Scale (SUS) & Trust:** Utilizing standardized Likert-scale instruments to measure clinician confidence in the "Cinematic Reasoning Replay" and "2D Confidence Space" visualizations.

### 8.3 Safety & Hallucination Auditing
- **Zero-Hallucination Prescription Guarantee:** Reporting the empirical failure rate of the Pharmacogenomic & Polypharmacy Guardrails. The target is a strictly bounded $0\%$ critical failure rate, proving the superiority of deterministic programmatic constraints overlaid on LLMs.
- **Guideline Drift Sensitivity:** Evaluating the Continuous Reversal Surveillance engine against historical data (e.g., injecting the 2017 ACC/AHA hypertension guideline shift and measuring the latency to systemic "Fragility Alert" propagation).

### 8.4 Ethical Constraints & Limitations Disclosure
Top-tier venues mandate robust discussion of limitations. The implementation and paper will formally address:
- **Algorithmic Bias:** Acknowledging and testing against the demographic limitations of the MIMIC-IV and CheXpert training sets.
- **Automation Bias:** Addressing the risk of clinicians over-relying on the system, detailing the UI friction (e.g., forced "Acknowledge Risk" buttons) intentionally designed to mitigate rubber-stamping.

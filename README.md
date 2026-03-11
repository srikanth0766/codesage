# CodeSage: Agentic AST-aware Smart Compiler

A next-generation, AI-powered system that goes beyond compiling code. CodeSage understands code architecture, detects smells, automatically refactors with AI, enforces CI/CD quality gates, and predicts agile technical debt risks using statistical modeling.

## 🌟 Key Capabilities

1. **Universal AST Analysis**: Parses Python and JavaScript into a unified AST schema.
2. **Code Smell Detection**: Identifies 6 structural code smells with confidence scores using heuristic thresholds (Long Method, God Class, Feature Envy, Deep Nesting, Large Parameter List, High Complexity).
3. **Agentic Refactoring**: Fixes code automatically using an open-source local LLM (Ollama), prioritizing syntax preservation and semantic correctness.
4. **Agile Risk Prediction**: Uses historical sprint data to forecast future technical debt risk via a Bayesian stochastic model.
5. **CI/CD Gatekeeper**: Blocks PRs that exceed defined code smell thresholds before they merge.
6. **Comprehensive Test Suite**: Proven reliability via a 15-category, 50+ case automated validation suite.

---

## 🏗️ Architecture

The system is divided into two parts:
- **Backend**: Python 3.10+ / FastAPI application powering the AST analysis, LLM agent, metrics extraction, and REST API.
- **Frontend**: Vanilla HTML/JS/CSS dashboard providing an interactive IDE-like experience, analytics charts (Chart.js), and system settings.

### Core Modules (Backend)
- `analyzers.universal_ast_analyzer`: Converts source code to AST.
- `analyzers.feature_extractor`: Calculates complexity, CBO, LOC, WMC.
- `analyzers.smell_detector`: Evaluates extracted features against smell thresholds.
- `refactor_agent.refactor_agent`: Orchestrates the LLM to apply clean code principles.
- `agile_risk.sprint_risk_model`: Calculates sprint risk probability.
- `main.py`: The FastAPI server exposing endpoints.

---

## 🚀 Step-by-Step Setup Guide

### Prerequisites
- **Python 3.10+** installed
- **pip** (Python package installer)
- **Ollama** installed locally (required for the Refactoring Agent)
- Modern Web Browser (Chrome, Firefox, Safari)

---

### Step 1: Install & Start Ollama (Required for AI Refactoring)

CodeSage uses local LLMs to keep your code private and avoid API fees.
1. Download and install Ollama from [ollama.com](https://ollama.com/).
2. Open your terminal and pull the recommended model (`qwen2.5:0.5b` or `llama3.2`):
   ```bash
   ollama pull qwen2.5:0.5b
   ```
3. Ensure the Ollama service is running in the background.

---

### Step 2: Setup the Backend

1. **Open a terminal** and navigate to the project directory:
   ```bash
   cd "path/to/compiler design project/backend"
   ```

2. **Create a Python Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *The server should now be running at `http://localhost:8000`.*

---

### Step 3: Run the Comprehensive Validation Suite

CodeSage includes a massive 15-category validation suite proving its integrity. You can run all tests and generate a report using the master script.

1. Keep the FastAPI server running and open a **new terminal tab**.
2. Navigate to the backend directory:
   ```bash
   cd "path/to/compiler design project/backend"
   ```
3. Run the automated test suite:
   ```bash
   bash run_all_tests.sh
   ```
   *This command runs the unit tests, integration tests, E2E tests, and chaos tests, generating an `integrity_report.txt` and a `test_report.json` in the `backend/tests/` folder.*

---

### Step 4: Start the Frontend Dashboard

CodeSage includes a sleek React-based web dashboard for Neural Auditing, Sprint Risk Analytics, and Terminal Streaming.

1. Open a **new terminal tab**.
2. Navigate to the frontend directory:
   ```bash
   cd "path/to/compiler design project/frontend"
   ```
3. Install dependencies and start the dev server:
   ```bash
   npm install
   npm run dev
   ```
4. Open your web browser and navigate to: **http://localhost:5173** (or the URL provided by Vite).
5. **Usage:**
   - **Sprint History:** Add, record, and view the number of smells and fixes across sprints.
   - **Analytics & Risk Prediction:** View visual charts showing your system's cumulative technical debt and risk predictions for future sprints.
   - **Neural Auditor:** Paste snippets of code into the analyzer to instantly detect architectural code smells like Long Methods and God Classes, with full metric transparency.
   - **Terminal:** View a live-streaming log of the backend Python server.

---

### Step 5: Using the VS Code Extension (IDE & Auto-Refactoring)

The true power of CodeSage is its editor integration via the VS Code extension, which provides inline code review and LLM-powered refactoring.

1. Open VS Code and navigate to the `vscode-extension` folder.
2. Open a terminal in that folder and run:
   ```bash
   npm install
   ```
3. Press **F5** in VS Code to launch the Extension Development Host.
4. In the new VS Code window, open any Python file.
5. Bring up the Command Palette (`Cmd+Shift+P` on Mac) and type **"Analyze Code with AI"**.
6. The extension will securely send your code to the local backend, detect runtime/logical errors, extract code smells, and provide **AI Refactoring suggestions** using your local Ollama model.

---

## 🧪 The 15-Category Test Suite

To ensure absolute reliability, CodeSage implements a rigorous validation suite covering:

1. **Compiler Core**: Lexical, Syntax, and AST integrity checks.
2. **Feature Extraction Validation**: Verifies cyclomatic complexity, CBO, WMC accuracy.
3. **ML Model Validation**: Tests the error detection logic bounds.
4. **Smell Detector**: Validates threshold logic for all 6 smell types.
5. **Refactor Safety**: Verifies that LLM output is always valid Python (Syntax Preservation) and implements Rollback on failure.
6. **CI/CD Gatekeeper**: Simulates 50 synthetic Pull Requests, enforcing block/pass logic.
7. **Agile Risk Prediction**: Validates the mathematical stability of the Bayesian stochastic drift model.
8. **Performance & Scalability**: Memory limits and cyclomatic extraction on high-branch functions.
9. **Security**: Verifies that user code is *parsed* as AST but never *executed*, preventing command injection.
10. **Data Integrity**: Validates the local datastore's atomic write limits.
11. **Chaos Testing**: Injects simulated failures (LLM timeout, DB crash) to prove graceful degradation without 500 errors.
12. **End-to-End System Tests**: Full pipeline from raw string to sprint analytics via HTTP.
13. **Regression Suite**: Validates output against 5 curated Baseline files.
14. **Observability Validation**: Logs, metrics, and API health checks.
15. **Acceptance Validator**: Weights all previous steps and mandates a final system Integrity Score ≥ 80%.

You can find the implementation of these tests in `backend/tests/`.

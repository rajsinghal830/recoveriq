# 💰 RecoverIQ — AI Revenue Recovery Agent

RecoverIQ is an AI-powered payment recovery system designed to help businesses recover revenue from failed payments.

It analyzes payment failures, evaluates recovery eligibility and priority, selects a recovery strategy, executes recovery actions, and records every decision in an auditable SQLite database.

## 🌐 Live Demo

🚀 **Live Dashboard:** https://recoveriq-69wqrcau3gsog2ndr8sbdk.streamlit.app/

💻 **GitHub Repository:** https://github.com/rajsinghal830/recoveriq

> The live deployment uses demo data and mock recovery tools for a safe Buildathon demonstration.

---

## 🎯 Problem

Failed payments create lost revenue and require manual follow-up. Different payment failures need different recovery strategies.

- Insufficient funds → retry later and remind the customer
- Expired card → ask the customer to update payment details
- Bank timeout → retry through an appropriate payment route
- Mandate failure → resend authorization
- Checkout abandonment → re-engage the customer
- Network error → retry when appropriate

RecoverIQ automates this workflow while keeping recovery decisions explainable and auditable.

---

## 🚀 How RecoverIQ Works

```text
Payment Failure
      ↓
Root Cause Detector
      ↓
Policy Engine
      ↓
Recovery Strategist
      ↓
Recovery Executor
      ↓
SQLite Audit Trail
      ↓
Streamlit Dashboard
```

**Core flow:** Failed Payment → Detection → Policy Evaluation → Strategy → Execution → Audit → Analytics

---

## 🤖 Multi-Agent Architecture

### Agent 1 — Root Cause Detector

Identifies why a payment failed.

Supported failure categories:

- `INSUFFICIENT_FUNDS`
- `CARD_EXPIRED`
- `BANK_TIMEOUT`
- `MANDATE_FAILED`
- `CHECKOUT_ABANDONED`
- `NETWORK_ERROR`

The detector can use Gemini when AI reasoning is required and includes a rule-based fallback for common failures.

### Policy Engine — Safety Layer

The policy engine provides deterministic and explainable guardrails before recovery execution.

It evaluates:

- Failure type
- Payment value
- Estimated recoverability
- Recovery priority
- Whether automated recovery is allowed
- Appropriate policy action

Example policy actions include `STANDARD_RECOVERY` and `PRIORITY_RECOVERY`.

### Agent 2 — Recovery Strategist

Selects the best recovery strategy using the failure reason, severity, recovery opportunity, payment information, retry history, and policy constraints.

### Agent 3 — Recovery Executor

Executes the selected recovery action through the available tools. Mock execution is supported for safe demonstrations.

---

## 💡 Recovery Strategies

| Failure Type | Recovery Strategy |
|---|---|
| `INSUFFICIENT_FUNDS` | Retry later + customer reminder |
| `CARD_EXPIRED` | Ask customer to update payment details |
| `BANK_TIMEOUT` | Retry through an appropriate payment route |
| `MANDATE_FAILED` | Resend eMandate authorization |
| `CHECKOUT_ABANDONED` | Customer re-engagement |
| `NETWORK_ERROR` | Immediate/controlled retry |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| AI | Google Gemini |
| Agent Framework | LangChain |
| Payment Integration | Razorpay tools / mock payment layer |
| Communication | Twilio tools / mock communication layer |
| Dashboard | Streamlit |
| Charts | Plotly |
| Database | SQLite |
| Console UI | Rich |

---

## 📁 Project Structure

```text
recoveriq/
│
├── agents/
│   ├── __init__.py
│   ├── detector.py
│   ├── strategist.py
│   ├── executor.py
│   └── policy.py
│
├── dashboard/
│   ├── __init__.py
│   └── app.py
│
├── data/
│   └── mock_failures.json
│
├── tools/
│   ├── __init__.py
│   ├── audit_tools.py
│   ├── comms_tools.py
│   └── razorpay_tools.py
│
├── config.py
├── orchestrator.py
├── webhook_simulator.py
├── recoveriq_audit.db
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/rajsinghal830/recoveriq.git
cd recoveriq
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
```

If your virtual environment is one directory above `recoveriq`:

```powershell
..\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a local `.env` file:

```env
GEMINI_API_KEY=your_gemini_key

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone
```

**Never commit real API keys, tokens, or secrets to GitHub.**

Use environment variables locally and deployment secrets for Streamlit Cloud.

---

## ▶️ Run the Recovery Engine

From the `recoveriq` directory:

```bash
python orchestrator.py
```

### Test with 3 events

```bash
python orchestrator.py --count 3
```

### Filter by failure type

```bash
python orchestrator.py --failure-type CARD_EXPIRED
```

### Reset the audit database and run a fresh demo

```bash
python orchestrator.py --reset
```

`--reset` clears previous audit data so the demonstration starts from a clean state.

---

## 📊 Run the Dashboard

From the `recoveriq` directory:

```bash
python -m streamlit run dashboard/app.py
```

Open:

```text
http://localhost:8501
```

The dashboard reads from the SQLite audit database and displays the latest recovery results.

---

## 📈 Dashboard Features

- 💳 Total unique payments
- ✅ Total recovered payments
- 📈 Recovery rate
- 💰 Amount recovered
- 🥧 Recovery outcome breakdown
- 📊 Recovery rate by failure reason
- 🎯 Recovery priority distribution
- 📋 Recovery by failure type
- 🗂️ Full audit log
- 🔍 Failure reason filters
- 🔍 Outcome filters
- 🔍 Priority filters
- 🔄 Optional auto-refresh

The audit log exposes fields including Payment ID, Customer, Amount, Failure Reason, Priority Score, Priority, Policy Action, Policy Allowed, Outcome, and Recovered Amount.

---

## 🧪 Demo Data

The project includes:

```text
data/mock_failures.json
```

The dataset contains simulated payment failure events covering multiple failure categories, allowing the complete workflow to be demonstrated without depending on production payment traffic.

---

## 🗃️ Audit Trail

RecoverIQ stores recovery information in SQLite.

The audit system tracks:

- Recovery runs
- Agent decisions
- Policy decisions
- Recovery actions
- Recovery outcomes
- Recovered amounts
- Timestamps

This provides traceability for every recovery decision.

---

## 🔒 Safety & Guardrails

RecoverIQ is designed for safe demonstration and controlled automation.

- Policy guardrails evaluate whether automated recovery is allowed.
- Payment and communication tools support mock execution.
- The demo does not need to charge real customers or send unwanted messages.
- API credentials must be stored in environment variables or deployment secrets.

---

## 🎥 Buildathon Demo Flow

```text
Payment failure occurs
        ↓
Detector identifies root cause
        ↓
Policy Engine evaluates eligibility + priority
        ↓
Strategist selects recovery strategy
        ↓
Executor performs recovery action
        ↓
Decision + action are recorded
        ↓
Dashboard displays recovery analytics
```

---

## 📊 Example Demo Metrics

A demo run can produce metrics such as:

| Metric | Example |
|---|---:|
| Unique Payments | 100 |
| Recovered Payments | 30 |
| Recovery Rate | 30.0% |
| Amount Recovered | ₹76,470.00 |

These values are based on a demo run and can change when the recovery simulation is executed again.

---

## 🧠 Why AI?

Traditional payment retry systems often apply the same recovery action to every failed payment.

RecoverIQ instead follows a decision-based workflow:

```text
Payment Failed
      ↓
Understand Why
      ↓
Evaluate Recovery Opportunity
      ↓
Apply Policy Guardrails
      ↓
Choose Best Strategy
      ↓
Execute Action
      ↓
Audit + Measure Recovery
```

This makes recovery more targeted, explainable, and easier to monitor.

---

## ☁️ Deployment

The dashboard is deployed on Streamlit Cloud.

**Live Dashboard:**  
https://recoveriq-69wqrcau3gsog2ndr8sbdk.streamlit.app/

Deployment entry point:

```text
dashboard/app.py
```

For deployment, select the GitHub repository, set `dashboard/app.py` as the main file, and configure required secrets in the deployment settings.

---

## 🚀 Future Improvements

- Real-time Razorpay webhook integration
- More payment failure categories
- ML-based recovery probability prediction
- Customer-level recovery scoring
- Better retry timing optimization
- A/B testing of recovery strategies
- Advanced notification personalization
- Production-grade persistent database
- Recovery revenue forecasting
- Real-time recovery monitoring

---

## 👨‍💻 Project

Built for the **Razorpay AI Builder / Buildathon**.

RecoverIQ focuses on turning failed payments into recoverable revenue through intelligent, automated, policy-controlled recovery workflows.

## 🔗 Links

🚀 **Live Dashboard:** https://recoveriq-69wqrcau3gsog2ndr8sbdk.streamlit.app/

💻 **GitHub Repository:** https://github.com/rajsinghal830/recoveriq

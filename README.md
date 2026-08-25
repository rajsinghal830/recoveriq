# 💰 RecoverIQ — AI Revenue Recovery Agent

RecoverIQ is an AI-powered payment recovery system designed to help businesses recover revenue from failed payments.

It analyzes payment failures, identifies the root cause, selects an appropriate recovery strategy, executes recovery actions, and records every decision in an audit database.

---

## 🎯 Problem

Failed payments create lost revenue and require manual follow-up.

Different payment failures need different recovery strategies.

For example:

- Insufficient funds → retry later
- Expired card → ask the customer to update the card
- Bank timeout → retry using another payment method
- Mandate failure → resend authorization
- Checkout abandonment → re-engage the customer

RecoverIQ automates this process.

---

## 🚀 How RecoverIQ Works

```text
Payment Failure
      │
      ▼
┌─────────────────────┐
│ Root Cause Detector │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Recovery Strategist │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Recovery Executor   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ SQLite Audit Trail  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Streamlit Dashboard │
└─────────────────────┘
```

---

## 🤖 AI Agents

### Agent 1 — Root Cause Detector

Identifies why a payment failed.

Supported failure categories:

- `INSUFFICIENT_FUNDS`
- `CARD_EXPIRED`
- `BANK_TIMEOUT`
- `MANDATE_FAILED`
- `CHECKOUT_ABANDONED`
- `NETWORK_ERROR`

The detector uses Gemini when AI reasoning is required and has a rule-based fallback for common failures.

### Agent 2 — Recovery Strategist

Selects the best recovery strategy based on:

- Failure reason
- Severity
- Recovery window
- Payment information
- Retry history

### Agent 3 — Recovery Executor

Executes the selected recovery action.

The project supports mock execution for safe demonstrations.

---

## 💡 Recovery Strategies

| Failure Type | Recovery Strategy |
|---|---|
| INSUFFICIENT_FUNDS | Retry on salary credit day + WhatsApp reminder |
| CARD_EXPIRED | Ask customer to update card |
| BANK_TIMEOUT | Retry through UPI / alternate route |
| MANDATE_FAILED | Resend eMandate authorization |
| CHECKOUT_ABANDONED | WhatsApp + voice re-engagement |
| NETWORK_ERROR | Immediate retry |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| AI | Google Gemini |
| Agent Framework | LangChain |
| Payment API | Razorpay |
| Communication | Twilio |
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
│   └── executor.py
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
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/rajsinghal830/recoveriq.git
```

Move into the project:

```bash
cd recoveriq
```

Create a virtual environment on Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file locally.

Example:

```env
GEMINI_API_KEY=your_gemini_key

RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE=your_twilio_phone
```

**Never commit real API keys or secrets to GitHub.**

The application reads credentials using environment variables.

---

## ▶️ Run RecoverIQ

Run the recovery engine:

```bash
python orchestrator.py
```

The system processes payment failure events and produces a recovery summary.

---

## 📊 Run the Dashboard

Start Streamlit:

```bash
python -m streamlit run dashboard/app.py
```

Open:

```text
http://localhost:8501
```

---

## ☁️ Streamlit Deployment

RecoverIQ can be deployed using Streamlit Cloud.

The dashboard automatically initializes the SQLite database and loads demo payment data when the deployed database is empty.

Secrets should be configured through Streamlit Cloud rather than committed to GitHub.

---

## 📈 Dashboard Features

The dashboard provides:

- 💳 Total unique payments
- ✅ Total recovered payments
- 📈 Recovery rate
- 💰 Amount recovered
- 🥧 Recovery outcome breakdown
- 📊 Recovery rate by failure reason
- 📋 Recovery by failure type
- 🗂️ Full audit log
- 🔍 Failure reason filters
- 🔍 Outcome filters
- 🔄 Optional auto-refresh

---

## 🧪 Demo Data

The project includes:

```text
data/mock_failures.json
```

This provides sample failed payment events for demonstrating the complete recovery workflow.

The dashboard can automatically seed demo data when the audit database is empty.

---

## 🗃️ Audit Trail

RecoverIQ stores recovery information in SQLite.

The audit system tracks:

- Recovery runs
- Agent decisions
- Recovery actions
- Recovery outcomes
- Recovered amounts
- Timestamps

This provides traceability for every recovery decision.

---

## 🔒 Safety

The project supports mock modes for external services so the Buildathon demonstration can run without sending real customer communications or performing unwanted live actions.

API credentials should always be stored as environment variables or deployment secrets.

---

## 🎥 Buildathon Demo Flow

```text
1. Payment failure occurs
          ↓
2. RecoverIQ receives the failure event
          ↓
3. Detector Agent identifies the root cause
          ↓
4. Strategist Agent selects a recovery strategy
          ↓
5. Executor Agent performs the recovery action
          ↓
6. Action is recorded in the audit database
          ↓
7. Recovery result is recorded
          ↓
8. Streamlit dashboard displays analytics
```

---

## 🌐 Live Demo

### RecoverIQ Dashboard

https://recoveriq-69wqrcau3gsog2ndr8sbdk.streamlit.app/

### GitHub Repository

https://github.com/rajsinghal830/recoveriq

---

## 💰 Example Recovery Scenarios

### Insufficient Funds

```text
Payment Failed
      ↓
INSUFFICIENT_FUNDS
      ↓
Medium Severity
      ↓
Schedule retry
      ↓
WhatsApp reminder
      ↓
Payment recovered
```

### Card Expired

```text
Payment Failed
      ↓
CARD_EXPIRED
      ↓
Ask customer to update card
      ↓
Provide payment link
      ↓
Retry payment
```

### Bank Timeout

```text
Payment Failed
      ↓
BANK_TIMEOUT
      ↓
Immediate retry
      ↓
Use alternate payment route
      ↓
Payment recovered
```

### Checkout Abandoned

```text
Checkout Started
      ↓
Customer leaves
      ↓
CHECKOUT_ABANDONED
      ↓
WhatsApp re-engagement
      ↓
Voice follow-up when appropriate
      ↓
Retry payment
```

---

## 🧠 Why AI?

Traditional payment retry systems often apply the same retry strategy to every failure.

RecoverIQ uses intelligent decision-making to select a strategy based on the reason for failure.

Instead of:

```text
Payment Failed → Retry Everything
```

RecoverIQ uses:

```text
Payment Failed
      ↓
Understand Why
      ↓
Choose Best Strategy
      ↓
Execute Action
      ↓
Measure Recovery
```

This makes the recovery process more targeted and reduces unnecessary retries and customer contact.

---

## 📊 Example Dashboard Metrics

A demo run can show metrics such as:

| Metric | Example |
|---|---:|
| Unique Payments | 100 |
| Recovered Payments | 30 |
| Recovery Rate | 30.0% |
| Amount Recovered | ₹76,470.00 |

These values are generated from the included demo data and may change depending on the recovery run.

---

## 🔄 Recovery Pipeline

```text
                    ┌──────────────────┐
                    │ Payment Failure  │
                    └────────┬─────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │  Detector Agent     │
                  │                     │
                  │ Root Cause Analysis │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Strategist Agent    │
                  │                     │
                  │ Recovery Strategy   │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Executor Agent      │
                  │                     │
                  │ Execute Recovery    │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Audit Database      │
                  │                     │
                  │ Decisions + Actions │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Streamlit Dashboard │
                  │                     │
                  │ Analytics + KPIs    │
                  └─────────────────────┘
```

---

## 🚀 Future Improvements

Possible future improvements include:

- Real-time Razorpay webhook integration
- More payment failure categories
- ML-based recovery probability prediction
- Customer-level recovery scoring
- Better retry timing optimization
- A/B testing of recovery strategies
- Advanced notification personalization
- Production-grade persistent database
- Recovery revenue forecasting

---

## 👨‍💻 Project

Built for the **Razorpay Buildathon**.

RecoverIQ focuses on turning failed payments into recoverable revenue through intelligent, automated recovery workflows.

---

## 📌 Repository

GitHub:

https://github.com/rajsinghal830/recoveriq

Live Dashboard:

https://recoveriq-69wqrcau3gsog2ndr8sbdk.streamlit.app/

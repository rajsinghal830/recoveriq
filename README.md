# ðŸ’° RecoverIQ â€” AI Revenue Recovery Agent

> **Razorpay Buildathon 2026 Â· Track 03: AI Revenue Recovery**

RecoverIQ is a multi-agent AI system that autonomously recovers failed payments.
It diagnoses *why* a payment failed, selects the *right* recovery strategy, and executes it â€”
with a full audit trail and measurable recovery outcomes.

---

## ðŸ—ï¸ Architecture

```
 Razorpay Webhook Stream
          â”‚
          â–¼
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚  Agent 1: Detector  â”‚  â† Classifies failure root cause (LLM + rules)
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â–¼
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚ Agent 2: Strategist â”‚  â† Builds recovery plan with compliance guardrails
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â–¼
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚  Agent 3: Executor  â”‚  â† Runs actions: retry / WhatsApp / voice / links
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
            â–¼
     SQLite Audit DB  â”€â”€â–º Streamlit Dashboard
```

---

## âš¡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API keys (optional â€” works in mock mode without keys)
```bash
# Windows
set GEMINI_API_KEY=your_gemini_key
set RAZORPAY_KEY_ID=rzp_test_xxxx
set RAZORPAY_KEY_SECRET=your_secret
```

### 3. Run the recovery pipeline
```bash
# Process all 100 mock failures
python orchestrator.py

# Process just 10 failures
python orchestrator.py --count 10

# Process only CARD_EXPIRED failures
python orchestrator.py --failure-type CARD_EXPIRED
```

### 4. Launch the dashboard
```bash
streamlit run dashboard/app.py
```

### 5. Simulate webhooks
```bash
python webhook_simulator.py --single          # 1 random event
python webhook_simulator.py --count 5         # first 5 events
```

---

## ðŸ› ï¸ Tech Stack

| Layer | Tool |
|---|---|
| LLM | Google Gemini 1.5 Flash |
| Agent Logic | Python classes (LangChain-ready) |
| Payment APIs | Razorpay SDK (mock mode included) |
| Comms | Twilio SMS / WhatsApp / Voice (mock mode) |
| Dashboard | Streamlit + Plotly |
| Audit DB | SQLite |
| Console UI | Rich |

---

## ðŸŽ¯ Recovery Strategies by Failure Type

| Failure | Strategy |
|---|---|
| INSUFFICIENT_FUNDS | WhatsApp reminder â†’ retry on salary day |
| CARD_EXPIRED | Payment link to update card |
| BANK_TIMEOUT | Immediate retry via UPI |
| MANDATE_FAILED | Re-send eMandate link |
| CHECKOUT_ABANDONED | WhatsApp + Hinglish voice call |
| NETWORK_ERROR | Instant retry |

---

## ðŸ“Š Demo Output (sample)

```
ðŸ’° RecoverIQ â€” AI Revenue Recovery Agent

Loaded 100 failure events

  RECOVERED   pay_001    NETWORK_ERROR          â‚¹   999.00
  RECOVERED   pay_002    CHECKOUT_ABANDONED     â‚¹   499.00
  FAILED      pay_003    INSUFFICIENT_FUNDS     â‚¹  1999.00
  ...

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚   RecoverIQ â€” Recovery Summary  â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ Total Processed  â”‚          100 â”‚
â”‚ Recovered        â”‚           71 â”‚
â”‚ Recovery Rate    â”‚        71.0% â”‚
â”‚ Amount Recovered â”‚  â‚¹52,341.00  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## ðŸ”’ Compliance & Stopping Rules

- Max **3 retry attempts** per payment
- No contact between **10 PM â€“ 8 AM**
- Max **2 outreach messages** per customer per day
- Escalate to human after **3 failed recoveries**
- Full audit trail for every decision

---

## ðŸ“ Project Structure

```
recoveriq/
â”œâ”€â”€ agents/
â”‚   â”œâ”€â”€ detector.py       # Agent 1: Root cause classifier
â”‚   â”œâ”€â”€ strategist.py     # Agent 2: Strategy planner
â”‚   â””â”€â”€ executor.py       # Agent 3: Action runner
â”œâ”€â”€ tools/
â”‚   â”œâ”€â”€ razorpay_tools.py # Razorpay API (mock + real)
â”‚   â”œâ”€â”€ comms_tools.py    # SMS / WhatsApp / Voice
â”‚   â””â”€â”€ audit_tools.py    # SQLite audit logger
â”œâ”€â”€ data/
â”‚   â””â”€â”€ mock_failures.json
â”œâ”€â”€ dashboard/
â”‚   â””â”€â”€ app.py            # Streamlit dashboard
â”œâ”€â”€ orchestrator.py       # Main pipeline
â”œâ”€â”€ webhook_simulator.py  # Webhook event simulator
â”œâ”€â”€ config.py             # All settings & API keys
â””â”€â”€ requirements.txt
```

# A.M.E. Setup Instructions

## PREREQUISITES
- Python 3.10+
- Razorpay test account/credentials
- (Optional) OpenAI API key for advanced natural language parsing

## INSTALLATION (WINDOWS)

1. **Open PowerShell** and navigate to the project:
   ```powershell
   cd "C:\Users\Devansh\.gemini\antigravity\scratch\ame-project"
   ```

2. **Create virtual environment**:
   ```powershell
   python -m venv .venv
   ```

3. **Activate it**:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(If PowerShell blocks scripts, use Command Prompt and run: `.venv\Scripts\activate.bat`)*

4. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

5. **Create Environment File**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` to include:
   ```env
   OPENAI_API_KEY=sk-...
   RAZORPAY_KEY_ID=rzp_test_...
   RAZORPAY_KEY_SECRET=...
   BACKEND_URL=http://localhost:8000
   ```
   *Note: NEVER use production Razorpay credentials. Use Test Mode only.*

## RUNNING THE APPLICATION

### Terminal 1 (Backend)
```bash
uvicorn main:app --reload --port 8000
```

### Terminal 2 (React Frontend)
```bash
cd frontend
npm install
npm run dev
```

*Note: The Streamlit fallback UI can still be started with `streamlit run app.py`.*

## HEALTH CHECK & TESTING
1. **Verify Backend**: Open your browser and go to `http://localhost:8000/`. You should see `{"status": "A.M.E. Server is live", ...}`.
2. **Open Frontend**: Navigate to `http://localhost:8501`.
3. **End-to-End Test**:
   - Go to **BUYER AGENT**.
   - Enter a query like: `"Find me 5 SaaS Pro licenses under ₹11,000"`.
   - Click "RUN BUYER AGENT".
   - Watch the agent discover, validate, and negotiate.
   - Click "PAY VIA RAZORPAY" (the modal will now pop out perfectly on the screen).
   - Enter test card details.
   - Click "CHECK PAYMENT STATUS" to complete the flow and verify the order is marked paid.
   - Check the **TRANSACTIONS** tab to see your completed deal.

## TROUBLESHOOTING
- **Backend Offline / Read timed out**: Ensure your backend terminal is running and not showing errors. If it fails instantly on checkout, verify your `RAZORPAY_KEY_ID` and `SECRET` are correct in `.env`.
- **OpenAI Unavailable**: The application will automatically fall back to deterministic regex matching for natural language requests.
- **Port 8000 Occupied**: Stop any existing processes on port 8000, or run uvicorn with `--port 8001` (if you do this, update `BACKEND_URL` in `.env`).

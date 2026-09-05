from datetime import datetime
from pathlib import Path
import os
import time
import json
import uuid
import re

try:
    import openai
except ImportError:
    openai = None

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="A.M.E. - Agentic Merchant Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://track-1-ai-growth-agentic-commerce.vercel.app",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"
RAZORPAY_REQUEST_TIMEOUT = 3
POLICY_VERSION = "v1"

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "catalog.json"
TRANSACTIONS_PATH = BASE_DIR / "transactions.json"

def load_catalog():
    try:
        with CATALOG_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, dict):
                return {"products": []}
            return data
    except FileNotFoundError:
        print(f"ERROR: catalog.json not found at {CATALOG_PATH}")
        return {"products": []}
    except Exception as e:
        print(f"ERROR: could not load catalog.json: {e}")
        return {"products": []}

catalog = load_catalog()

def load_transactions():
    try:
        with TRANSACTIONS_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
            if not isinstance(data, list):
                return []
            return data
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"ERROR: could not load transactions.json: {e}")
        return []

def save_transaction(record):
    transactions = load_transactions()
    transactions.append(record)
    try:
        with TRANSACTIONS_PATH.open("w", encoding="utf-8") as file:
            json.dump(transactions, file, indent=2)
    except Exception as e:
        print(f"ERROR: could not save to transactions.json: {e}")

def update_transaction_status(order_id, status):
    transactions = load_transactions()
    updated = False
    for t in transactions:
        if t.get("razorpay_order_id") == order_id:
            t["status"] = status
            updated = True
            break
    if updated:
        try:
            with TRANSACTIONS_PATH.open("w", encoding="utf-8") as file:
                json.dump(transactions, file, indent=2)
        except Exception as e:
            print(f"ERROR: could not update transactions.json: {e}")
    else:
        print(f"WARNING: No transaction found matching Razorpay order ID {order_id}")

class NegotiationRequest(BaseModel):
    sku: str
    requested_quantity: int
    requested_discount_pct: float

class IntentRequest(BaseModel):
    query: str

class CounterOfferRequest(BaseModel):
    razorpay_order_id: str
    sku: str
    buyer_decision: str

class AuthRequest(BaseModel):
    action: str
    device: str

def razorpay_credentials():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay credentials are missing. "
            "Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env."
        )

    return key_id, key_secret

def create_razorpay_order(
    *,
    amount_paise: int,
    sku: str,
    quantity: int,
    negotiation_status: str,
):
    """
    Create a Razorpay TEST-MODE order with a hard network timeout.
    Returns (order_id, key_id, error).
    """
    try:
        key_id, key_secret = razorpay_credentials()

        response = requests.post(
            f"{RAZORPAY_API_BASE}/orders",
            auth=(key_id, key_secret),
            json={
                "amount": amount_paise,
                "currency": "INR",
                "receipt": f"ame_{sku}_{int(time.time())}"[:40],
                "notes": {
                    "sku": sku,
                    "requested_quantity": str(quantity),
                    "negotiation_status": negotiation_status,
                },
            },
            timeout=RAZORPAY_REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        order = response.json()

        order_id = order.get("id")
        if not order_id:
            return None, key_id, "Razorpay returned no order ID."

        return order_id, key_id, None

    except requests.exceptions.Timeout:
        return (
            None,
            os.getenv("RAZORPAY_KEY_ID"),
            f"Razorpay API timed out after {RAZORPAY_REQUEST_TIMEOUT} seconds.",
        )

    except requests.exceptions.HTTPError as e:
        detail = e.response.text if e.response is not None else str(e)
        return (
            None,
            os.getenv("RAZORPAY_KEY_ID"),
            f"Razorpay API rejected the order: {detail}",
        )

    except requests.exceptions.RequestException as e:
        return (
            None,
            os.getenv("RAZORPAY_KEY_ID"),
            f"Razorpay API request failed: {e}",
        )

    except Exception as e:
        return (
            None,
            os.getenv("RAZORPAY_KEY_ID"),
            f"Razorpay order creation failed: {e}",
        )

@app.get("/")
def health_check():
    return {
        "status": "A.M.E. Server is live",
        "version": "1.0.0",
    }

@app.get("/catalog")
def get_catalog():
    return catalog

@app.post("/agent/buyer/intent")
def parse_buyer_intent(req: IntentRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and openai:
        try:
            client = openai.OpenAI(api_key=api_key, max_retries=0)
            system_prompt = (
                "You are an AI assistant parsing buyer queries for B2B negotiation. "
                "Extract the SKU, requested quantity, and requested discount percentage (0-100). "
                f"Available products: {json.dumps(catalog.get('products', []))}\n"
                "Return ONLY a JSON object with keys: sku, requested_quantity, requested_discount_pct. "
                "Do not include markdown blocks."
            )
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": req.query}
                ],
                temperature=0,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            parsed = json.loads(content.strip())
            return {
                "sku": parsed.get("sku", ""),
                "requested_quantity": int(parsed.get("requested_quantity", 1)),
                "requested_discount_pct": float(parsed.get("requested_discount_pct", 0.0))
            }
        except Exception as e:
            print(f"OpenAI parsing failed: {e}")
            pass
    
    query = req.query.lower()
    sku = "SaaS-PRO-1M" if ("saas" in query or "pro" in query) else "API-CRED-10K" if "api" in query else "UNKNOWN"
    
    qty_match = re.search(r"(\d+)\s*(?:\w+\s*){0,2}(?:licenses|users|units|months)", query)
    if not qty_match:
        qty_match = re.search(r"\b(\d+)\b", query)
    qty = int(qty_match.group(1)) if qty_match else 1
    
    budget_match = re.search(r"(?:under|budget|₹|rs\.?)\s*(\d+(?:,\d+)*)", query)
    discount = 0.0
    if budget_match:
        budget = float(budget_match.group(1).replace(",", ""))
        base_price = 0
        for p in catalog.get("products", []):
            if p.get("sku") == sku:
                base_price = p.get("base_price_inr", 0)
                break
        if base_price > 0:
            total_base = base_price * qty
            if budget < total_base:
                discount = round(((total_base - budget) / total_base) * 100.0, 2)
    else:
        discount_match = re.search(r"(\d+(?:\.\d+)?)\s*%", query)
        discount = float(discount_match.group(1)) if discount_match else 0.0
    
    return {
        "sku": sku,
        "requested_quantity": qty,
        "requested_discount_pct": discount
    }

@app.get("/transactions")
def get_transactions():
    return load_transactions()

@app.post("/agent/respond-to-counter")
def respond_to_counter(req: CounterOfferRequest):

    tx_id = str(uuid.uuid4())
    tx_record = {
        "transaction_id": tx_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "sku": req.sku,
        "requested_quantity": req.requested_quantity,
        "requested_discount_pct": req.requested_discount_pct,
        "status": status,
        "negotiated_unit_price": round(discounted_unit_price, 2),
        "total_negotiated_price_inr": round(total_price, 2),
        "razorpay_order_id": razorpay_order_id,
        "merchant_auth": None,
        "auth_device": None
    }
    save_transaction(tx_record)

    response["transaction_id"] = tx_id
    response["merchant_auth"] = None
    return response



@app.get("/agent/authorization/{token}")
def get_auth_status(token: str):
    transactions = load_transactions()
    for t in transactions:
        if t.get("transaction_id") == token:
            return {
                "transaction_id": token,
                "merchant_auth": t.get("merchant_auth"),
                "auth_device": t.get("auth_device"),
                "sku": t.get("sku"),
                "requested_quantity": t.get("requested_quantity"),
                "requested_discount_pct": t.get("requested_discount_pct"),
                "total_negotiated_price_inr": t.get("total_negotiated_price_inr"),
                "negotiated_unit_price": t.get("negotiated_unit_price"),
                "razorpay_order_id": t.get("razorpay_order_id"),
                "razorpay_key_id": razorpay_credentials()[0]
            }
    raise HTTPException(status_code=404, detail="Transaction not found.")

@app.post("/agent/authorization/{token}")
def update_auth_status(token: str, req: AuthRequest):
    transactions = load_transactions()
    updated = False
    new_auth = "APPROVED" if req.action == "APPROVE" else "DECLINED"
    
    for t in transactions:
        if t.get("transaction_id") == token:
            if t.get("merchant_auth") is None:
                t["merchant_auth"] = new_auth
                t["auth_device"] = req.device
                updated = True
            break
            
    if updated:
        try:
            import json
            from pathlib import Path
            TRANSACTIONS_PATH = Path("transactions.json")
            with TRANSACTIONS_PATH.open("w", encoding="utf-8") as file:
                json.dump(transactions, file, indent=2)
            return {"status": "SUCCESS", "merchant_auth": new_auth}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Could not save auth state.")
    else:
        return {"status": "NO_UPDATE_NEEDED"}

@app.get("/agent/payment-status/{order_id}")

def get_payment_status(order_id: str):
    """
    Fetches the REAL Razorpay TEST-MODE order status.
    Returns Razorpay's status vocabulary without guessing.
    """

    try:
        key_id, key_secret = razorpay_credentials()

        response = requests.get(
            f"{RAZORPAY_API_BASE}/orders/{order_id}",
            auth=(key_id, key_secret),
            timeout=RAZORPAY_REQUEST_TIMEOUT,
        )

        response.raise_for_status()
        order = response.json()

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Razorpay API timed out after "
                f"{RAZORPAY_REQUEST_TIMEOUT} seconds."
            ),
        )

    except requests.exceptions.HTTPError as e:
        detail = e.response.text if e.response is not None else str(e)
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay rejected the status request: {detail}",
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach Razorpay: {e}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not fetch order status from Razorpay: {e}",
        )

    status = order.get("status")
    if status == "paid":
        update_transaction_status(order_id, "PAID")

    return {
        "order_id": order.get("id"),
        "status": status,
        "amount": order.get("amount"),
        "amount_paid": order.get("amount_paid"),
        "attempts": order.get("attempts"),
        "currency": order.get("currency"),
    }

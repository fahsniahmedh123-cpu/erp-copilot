"""
Tool 4: call_list_today
Returns prioritized list of customers to call today.
Uses real business rules:
  CASH bills   → should be collected immediately
  CREDIT bills → cheque must be received within 45 days
"""
import httpx
from auth import get_token
from config import FINANCE_API_BASE_URL


def call_list_today() -> list[dict]:
    """
    Returns today's call list sorted by priority.

    Priority:
    1. CHEQUE BOUNCED     → urgent, needs immediate recovery
    2. CASH UNPAID        → should have been collected on delivery
    3. NO CHEQUE RECEIVED → credit bill past 45 days
    4. REMINDER DUE       → manual reminder set by accountant
    """
    try:
        response = httpx.get(
            f"{FINANCE_API_BASE_URL}/copilot/bills/call-list",
            headers={"Authorization": f"Bearer {get_token()}"},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        return [
            {
                "call_reason":       item.get("callReason"),
                "customer_name":     item.get("customerName"),
                "phone":             item.get("phone"),
                "area":              item.get("area"),
                "tier":              item.get("tier"),
                "business":          item.get("business"),
                "bill_number":       item.get("billNumber"),
                "bill_type":         item.get("billType"),
                "bill_date":         item.get("billDate"),
                "balance_remaining": item.get("balanceRemaining"),
                "days_since_bill":   item.get("daysSinceBill"),
                "days_overdue":      item.get("daysOverdue"),
                "reminder_date":     item.get("reminderDate"),
                "reminder_note":     item.get("reminderNote"),
            }
            for item in data
        ]

    except httpx.HTTPStatusError as e:
        return {"error": f"FMS API error: {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"error": "FMS API timeout"}
    except Exception as e:
        return {"error": str(e)}
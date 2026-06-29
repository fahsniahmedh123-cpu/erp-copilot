"""
Tool 3: customer_profile
Returns everything about a specific customer.
Answers: "Tell me everything about Janalanka Textile"
         "What does VISVAMS owe us?"
"""
import httpx
from auth import get_token
from config import FINANCE_API_BASE_URL


def customer_profile(name: str) -> dict:
    """
    Returns full customer profile including all unpaid bills,
    payment history and total outstanding.

    Args:
        name: Customer name — fuzzy matched
    """
    try:
        response = httpx.get(
            f"{FINANCE_API_BASE_URL}/copilot/customers/profile",
            params={"name": name},
            headers={"Authorization": f"Bearer {get_token()}"},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        # Map customer fields
        customer = data.get("customer", {})
        summary  = data.get("summary", {})

        # Map unpaid bills
        unpaid_bills = [
            {
                "bill_id":           bill.get("billId"),
                "bill_number":       bill.get("billNumber"),
                "business":          bill.get("business"),
                "bill_type":         bill.get("billType"),
                "bill_date":         bill.get("billDate"),
                "total_amount":      bill.get("totalAmount"),
                "amount_paid":       bill.get("amountPaid"),
                "balance_remaining": bill.get("balanceRemaining"),
                "status":            bill.get("status"),
                "days_since_bill":   bill.get("daysSinceBill"),
                "is_overdue":        bill.get("isOverdue"),
                "overdue_reason":    bill.get("overdueReason"),
                "days_overdue":      bill.get("daysOverdue"),
            }
            for bill in data.get("unpaidBills", [])
        ]

        # Map payment history
        payment_history = [
            {
                "payment_id":    payment.get("paymentId"),
                "bill_number":   payment.get("billNumber"),
                "amount":        payment.get("amount"),
                "payment_type":  payment.get("paymentType"),
                "status":        payment.get("status"),
                "payment_date":  payment.get("paymentDate"),
                "cheque_number": payment.get("chequeNumber"),
                "bank_name":     payment.get("bankName"),
                "return_reason": payment.get("returnReason"),
            }
            for payment in data.get("paymentHistory", [])
        ]

        # Map reminders
        reminders = [
            {
                "reminder_date": reminder.get("reminderDate"),
                "note":          reminder.get("note"),
                "created_by":    reminder.get("createdBy"),
                "bill_number":   reminder.get("billNumber"),
            }
            for reminder in data.get("reminders", [])
        ]

        return {
            "customer": {
                "name":      customer.get("name"),
                "phone":     customer.get("phone"),
                "area":      customer.get("area"),
                "tier":      customer.get("tier"),
                "shop_type": customer.get("shopType"),
                "active":    customer.get("active"),
            },
            "summary": {
                "unpaid_bill_count":  summary.get("unpaidBillCount"),
                "total_outstanding":  float(summary.get("totalOutstanding") or 0),
                "oldest_unpaid_days": summary.get("oldestUnpaidDays"),
                "oldest_bill_date":   summary.get("oldestBillDate"),
            },
            "unpaid_bills":    unpaid_bills,
            "payment_history": payment_history,
            "reminders":       reminders
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Customer '{name}' not found"}
        return {"error": f"FMS API error: {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"error": "FMS API timeout"}
    except Exception as e:
        return {"error": str(e)}
"""
Tool 1: outstanding_bills
Returns unpaid/partially paid bills with customer contact info.
Supports filtering by business, area, tier, min_days, customer name.
Includes overdue logic based on real business rules:
  CASH   → overdue immediately if unpaid
  CREDIT → overdue after 45 days with no cheque received
"""
# from db.database import query
import httpx
from auth import get_token
from config import FINANCE_API_BASE_URL


def outstanding_bills(
    business: str = None,
    area: str = None,
    tier: str = None,
    min_days: int = None,
    customer: str = None,
    overdue_only: bool = False
) -> list[dict]:
    """
    Fetch outstanding bills.

    Args:
        business     : RAINCO / PLASTIC / STATIONERY / HARDWARE / RETAIL_SHOP
        area         : Badulla / Welimada / Haputale / Bandarawela / Ella etc.
        tier         : Platinum / Gold / Silver / Bronze / Emergency Top-up
        min_days     : Only bills older than N days
        customer     : Fuzzy search on customer name
        overdue_only : If True, only return overdue bills
    """
    # conditions = ["1=1"]
    params = {}

    if business:
        params["business"] = business

    if area:
        params["area"] = area

    if tier:
        params["tier"] = tier

    if min_days:
        params["min_days"] = min_days

    if customer:
        params["customer"] = customer

    if overdue_only:
        params["overdueOnly"] = True

    # where_clause = " AND ".join(conditions)

    # sql = f"""
    #     SELECT
    #         bill_id,
    #         bill_number,
    #         customer_name,
    #         phone,
    #         area,
    #         tier,
    #         shop_type,
    #         business,
    #         bill_type,
    #         bill_date,
    #         total_amount,
    #         amount_paid,
    #         balance_remaining,
    #         status,
    #         days_since_bill,
    #         is_overdue,
    #         overdue_reason,
    #         days_overdue
    #     FROM outstanding_bills_view
    #     WHERE {where_clause}
    #     ORDER BY
    #         -- Overdue bills first
    #         is_overdue DESC,
    #         -- Then by overdue reason severity
    #         CASE overdue_reason
    #             WHEN 'CHEQUE BOUNCED'       THEN 1
    #             WHEN 'CASH UNPAID'          THEN 2
    #             WHEN 'NO CHEQUE RECEIVED'   THEN 3
    #             ELSE 4
    #         END,
    #         -- Then by tier
    #         CASE tier
    #             WHEN 'Platinum'         THEN 1
    #             WHEN 'Gold'             THEN 2
    #             WHEN 'Silver'           THEN 3
    #             WHEN 'Bronze'           THEN 4
    #             WHEN 'Emergency Top-up' THEN 5
    #             ELSE 6
    #         END,
    #         days_overdue DESC
    # """

    # rows = query(sql, params)

    # # Serialize dates
    # for row in rows:
    #     if row.get("bill_date"):
    #         row["bill_date"] = str(row["bill_date"])

    # return rows

    try:
        response = httpx.get(
            f"{FINANCE_API_BASE_URL}/copilot/bills/outstanding",
            params=params,
            headers={"Authorization": f"Bearer {get_token()}"},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        return [
            {
                "bill_id":           item.get("billId"),
                "bill_number":       item.get("billNumber"),
                "customer_name":     item.get("customerName"),
                "phone":             item.get("phone"),
                "area":              item.get("area"),
                "tier":              item.get("tier"),
                "shop_type":         item.get("shopType"),
                "business":          item.get("business"),
                "bill_type":         item.get("billType"),
                "bill_date":         item.get("billDate"),
                "total_amount":      item.get("totalAmount"),
                "amount_paid":       item.get("amountPaid"),
                "balance_remaining": item.get("balanceRemaining"),
                "status":            item.get("status"),
                "days_since_bill":   item.get("daysSinceBill"),
                "is_overdue":        item.get("isOverdue"),
                "overdue_reason":    item.get("overdueReason"),
                "days_overdue":      item.get("daysOverdue"),
            }
            for item in data
        ]

    except httpx.HTTPStatusError as e:
        return {"error": f"FMS API error: {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"error": "FMS API timeout"}
    except Exception as e:
        return {"error": str(e)}

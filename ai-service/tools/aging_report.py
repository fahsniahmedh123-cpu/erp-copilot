"""
Tool 2: aging_report
Groups outstanding bills into age buckets per business.
Answers: "How is Rainco doing?", "Which business has the oldest debts?"
"""
import httpx
from auth import get_token
from config import FINANCE_API_BASE_URL


def aging_report(business: str = None) -> dict:
    """
    Returns outstanding bills grouped into aging buckets.

    Args:
        business: Optional — RAINCO / PLASTIC / STATIONERY / HARDWARE / RETAIL_SHOP
                  If None, returns all businesses.
    """
    params = {}
    if business:
        params["business"] = business.upper()

    try:
        response = httpx.get(
            f"{FINANCE_API_BASE_URL}/copilot/bills/aging",
            params=params,
            headers={"Authorization": f"Bearer {get_token()}"},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()

        # Map camelCase fields to snake_case
        result = {}
        for biz, buckets in data.items():
            result[biz] = {
                "0_30_days": {
                    "count":  buckets.get("count0to30", 0),
                    "amount": float(buckets.get("amount0to30", 0))
                },
                "31_60_days": {
                    "count":  buckets.get("count31to60", 0),
                    "amount": float(buckets.get("amount31to60", 0))
                },
                "61_90_days": {
                    "count":  buckets.get("count61to90", 0),
                    "amount": float(buckets.get("amount61to90", 0))
                },
                "90_plus_days": {
                    "count":  buckets.get("count90plus", 0),
                    "amount": float(buckets.get("amount90plus", 0))
                },
                "total_bills":       buckets.get("totalBills", 0),
                "total_outstanding": float(buckets.get("totalOutstanding", 0)),
                "oldest_days":       buckets.get("oldestDays", 0)
            }

        return result

    except httpx.HTTPStatusError as e:
        return {"error": f"FMS API error: {e.response.status_code}"}
    except httpx.TimeoutException:
        return {"error": "FMS API timeout"}
    except Exception as e:
        return {"error": str(e)}
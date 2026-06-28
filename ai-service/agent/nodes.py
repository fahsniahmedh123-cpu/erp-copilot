"""
nodes.py - Langraph agent nodes
Each node is one step in the agent's thinking process:

1. classify -> what is the user asking?
2. execute -> call the right tool
3. respond -> format the answer in plain English
"""

import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import GEMINI_API_KEY
from tools.outstanding_bills import outstanding_bills
from tools.aging_report import aging_report
from tools.customer_profile import customer_profile
from tools.call_list_today import call_list_today

# LLM setup
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1
)

SYSTEM_PROMPT = """
You are an ERP Copilot for a retail and wholesale busines in Sri Lanka.
You help the owner and accountants understand their financial data.

The business has 5 units: RAINCO, PLASTIC, STATIONERY, HARDWARE, RETAIL_SHOP.
Customers are in these exact areas:
Ambagasdowa, Badalkumbura, Badulla, Bandarawela, Beragala,
Bogakumbura, Boralanda, Demodara, Diyatalawa, Ella,
Etampitiya, Haldummulla, Hali-Ela, Hasalaka, Haputale,
Hopton, Kandaketiya, Keppatipola, Kumbalwela, Lunugala,
Lunuwatta, Mahiyanganaya, Meegahakivula, Passara,
Uva-Paranagama, Welimada.
Customers tiers: Platinum, Gold, Silver, Bronze, Emergency Top-up.

Bill rules:
- CASH bills: payment collected immediately on delivery
- CREDIT bills: cheque must be received within 45 days
- Bounced cheques are urgent

You have access to these tools:
- outstanding_bills : who owes money, filter by area/tier/business
- aging_report : outstanding grouped by age buckets per business
- customer_profile: full profile for one customer
- call_list_today : prioritized list of who to call today

Always answer in clear, concise English.
User LKR for currency amounts.
When listing customers, always show their phone number.
"""

# Node 1: Classify
def classify_node(state: dict) -> dict:
    """
    Decides which tool to call based on the user's message.
    Returns the tool name and extracted parameters.
    """
    message = state["message"]

    classification_prompt = f"""
    Analyze the question and decide which tool to call.

    Question: "{message}"

    Available tools:
    1. outstanding_bills - who owes money
       Parameters: business, area, tier, min_days, customer, overdue_only
    
    2. aging_report - aging buckets per business
       Parameters: business (optional)

    3. customer_profile - full profile for one customer
       Parameters: name (required)
    
    4. call_list_today - who to call today
       Parameters: none

    Respond ONLY with valid JSON like this:
    {{
        "tool": "tool_name",
        "params": {{
            "param1": "value1"
        }},
        "reasoning": "one line why"
    }}

    Rules:
    - If asking about one specific customer -> customer_profile
    - If asking who to call / reminders -> call_list_today
    - If asking about aging / how old debts are -> aging_report
    - If asking about outstanding / who owes / unpaid -> outstanding_bills
    - For outstanding_bills set overdue_only=true if asking about overdue specifically
    - Extract area from: Ambagasdowa, Badalkumbura, Badulla, Bandarawela, 
      Beragala, Bogakumbura, Boralanda, Demodara, Diyatalawa, Ella, Etampitiya,
      Haldummulla, Hali-Ela, Hasalaka, Haputale, Hopton, Kandaketiya, 
      Keppatipola, Kumbalwela, Lunugala, Lunuwatta, Mahiyanganaya, 
      Meegahakivula, Passara, Uva-Paranagama, Welimada
    - Match user input to closest area name exactly
    - Extract tier names exactly (Platinum, Gold, Silver, Bronze, Emergency Top-up)
    - Extract business names in uppercase (RAINCO, PLASTIC etc.)
"""
    
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=classification_prompt)
    ])

    # parse JSON response
    try: 
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        classification = json.loads(raw.strip())

    except Exception as e:
        # default fallback
        classification = {
            "tool": "outstanding_bills",
            "params": {},
            "reasoning": f"Parse error: {e} - defaulting to outstanding_bills"
        }

    return {
        **state,
        "tool": classification.get("tool"),
        "params": classification.get("params", {}),
        "reasoning": classification.get("reasoning")
    }

# Node 2 : Execute
def execute_node(state: dict) -> dict:
    """
    Calls the selected tool with extracted parameters.
    Returns raw tool data.
    """

    tool = state.get("tool")
    params = state.get("params", {})

    try: 
        if tool == "outstanding_bills":
            result = outstanding_bills(**params)
        
        elif tool == "aging_report":
            result = aging_report(**params)

        elif tool == "customer_profile":
            result = customer_profile(**params)
        
        elif tool == "call_list_today":
            result = call_list_today()

        else:
            result = {"error": f"Unknown tool: {tool}"}

    except Exception as e: 
        result = {"error": f"Toll execution failed: {str(e)}"}

    return {
        **state,
        "tool_result": result
    }

# Node 3 : Respond
def respond_node(state: dict) -> dict:
    """
    Takes the raw tool result and formats it into 
    a clear, natural language answer for the user.
    """
    message = state["message"]
    tool = state.get("tool")
    tool_result = state.get("tool_result")

    response_prompt = f"""
    The user asked: "{message}"

    You called the {tool} tool and got this data:
    {json.dumps(tool_result, indent=2, default=str)}

    Write a clear, helpful answer in plain English.

    Guidelines:
    - Be concise but complete
    - Use LKR for all amounts
    - Format amounts with commas (LKR 95,000)
    - Show phone numbers when available
    - For lists, show max 10 items then summarize
    - If data is empty, say so clearly
    - Highlight urgent items (bounced cheques, very old bills)
    - End with a helpful suggestion if relevant
    """

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=response_prompt)
    ])

    return {
        **state,
        "response": response.content
    }
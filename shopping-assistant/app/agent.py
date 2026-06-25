from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.workflow import Workflow

import os
from dotenv import load_dotenv

# Load environment variables from the project root .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

from app.tools import process_cart_checkout

# Securely load the Gemini API key from environment variables
model = Gemini(
    model="gemini-3.1-flash-lite",
    api_key=os.environ.get("GEMINI_API_KEY", "mock-key-value-12345"),
)

# In-memory discount redemption store (simulating database state)
DISCOUNT_STORE: dict[str, bool] = {"WELCOME50": False, "SUMMER20": False}


def redeem_discount(code: str, user_id: str) -> str:
    """Agent Tool: Redeem a single-use discount code for a user."""
    if code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."
    if DISCOUNT_STORE[code]:
        return "Error: Discount code has already been redeemed."
    if not user_id or user_id.startswith("guest_"):
        return "Error: Registered user account required to redeem discounts."

    DISCOUNT_STORE[code] = True
    return f"Success: Discount code {code} redeemed successfully for user {user_id}."


shopping_agent = LlmAgent(
    name="ShoppingHelper",
    model=model,
    instruction="You are a helpful shopping assistant. Use your tools to redeem discount codes for users, and process checkouts for shopping carts.",
    tools=[redeem_discount, process_cart_checkout],
)

root_workflow = Workflow(
    name="shopping_assistant_workflow", edges=[("START", shopping_agent)]
)

root_agent = root_workflow

app = App(name="app", root_agent=root_workflow)

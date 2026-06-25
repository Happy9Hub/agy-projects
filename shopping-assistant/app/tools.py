# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tools for the AI Shopping Assistant."""

# Mock database for registered user IDs
REGISTERED_USER_IDS = {"user_123", "user_456", "alice", "bob"}

# Mock database of valid discount codes
VALID_DISCOUNT_CODES = {
    "WELCOME50": "50% off",
    "SUMMER20": "20% off",
}

# In-memory store for redeemed discount codes (globally single-use)
REDEEMED_CODES = set()


def redeem_discount_code(code: str, user_id: str) -> dict:
    """Redeem a discount code for a registered user.

    Args:
        code: The discount code to redeem (e.g. WELCOME50, SUMMER20).
        user_id: The ID of the registered user redeeming the code.

    Returns:
        A dictionary with a success/failure status and details.
    """
    normalized_code = code.strip().upper()
    normalized_user_id = user_id.strip()

    if normalized_user_id not in REGISTERED_USER_IDS:
        return {
            "status": "failure",
            "message": f"User ID '{normalized_user_id}' is not registered. A registered user ID is required to redeem discount codes.",
        }

    if normalized_code not in VALID_DISCOUNT_CODES:
        return {
            "status": "failure",
            "message": f"Discount code '{normalized_code}' is invalid.",
        }

    if normalized_code in REDEEMED_CODES:
        return {
            "status": "failure",
            "message": f"Discount code '{normalized_code}' has already been redeemed. Each code can only be redeemed once.",
        }

    # Mark the code as redeemed
    REDEEMED_CODES.add(normalized_code)

    return {
        "status": "success",
        "message": f"Successfully redeemed code '{normalized_code}' for user '{normalized_user_id}'. Applied {VALID_DISCOUNT_CODES[normalized_code]}.",
    }


# Mock database for shopping carts
CARTS_DB = {
    "cart_123": {
        "user_id": "user_123",
        "items": [{"name": "Premium Wireless Headphones", "price": 150.0, "quantity": 1}],
        "status": "active",
    },
    "cart_456": {
        "user_id": "user_456",
        "items": [
            {"name": "Ergonomic Office Chair", "price": 300.0, "quantity": 1},
            {"name": "Desk Mat", "price": 25.0, "quantity": 2},
        ],
        "status": "active",
    },
    "guest_cart_789": {
        "user_id": "guest_789",
        "items": [{"name": "USB-C Cable", "price": 15.0, "quantity": 3}],
        "status": "active",
    }
}

# Mock database of processed orders
ORDERS_DB = {}


def process_cart_checkout(cart_id: str, user_id: str, discount_code: str | None = None) -> dict:
    """Process checkout for a shopping cart and apply a discount code if provided.

    Args:
        cart_id: The ID of the cart to check out.
        user_id: The ID of the user requesting checkout.
        discount_code: Optional discount code to apply.

    Returns:
        A dictionary indicating success or error status and order details.
    """
    normalized_cart_id = cart_id.strip()
    normalized_user_id = user_id.strip()

    # 1. Cart Existence Validation
    if normalized_cart_id not in CARTS_DB:
        return {
            "status": "failure",
            "message": f"Cart ID '{normalized_cart_id}' not found.",
        }

    cart = CARTS_DB[normalized_cart_id]

    # 2. Cart State Transition Check (Double Checkout Prevention)
    if cart["status"] != "active":
        return {
            "status": "failure",
            "message": f"Cart '{normalized_cart_id}' cannot be checked out because its status is '{cart['status']}'.",
        }

    # 3. Ownership Verification (Spoofing Prevention)
    if cart["user_id"] != normalized_user_id:
        return {
            "status": "failure",
            "message": f"Access Denied: User '{normalized_user_id}' does not own cart '{normalized_cart_id}'.",
        }

    # Calculate subtotal
    subtotal = sum(item["price"] * item.get("quantity", 1) for item in cart["items"])
    discount_amount = 0.0

    # 4. Discount Code Application (if provided and valid)
    if discount_code and discount_code.strip() and discount_code.strip().lower() not in ("none", "null", "undefined"):
        normalized_code = discount_code.strip().upper()

        # Check discount restrictions
        redemption_result = redeem_discount_code(normalized_code, normalized_user_id)
        if redemption_result["status"] == "failure":
            return {
                "status": "failure",
                "message": f"Checkout aborted. Discount error: {redemption_result['message']}",
            }

        # Apply the discount (WELCOME50 = 50%, SUMMER20 = 20%)
        if normalized_code == "WELCOME50":
            discount_amount = subtotal * 0.5
        elif normalized_code == "SUMMER20":
            discount_amount = subtotal * 0.2

    total = subtotal - discount_amount

    # Create the order
    order_id = f"order_{normalized_cart_id}_{len(ORDERS_DB) + 1}"
    order_details = {
        "order_id": order_id,
        "cart_id": normalized_cart_id,
        "user_id": normalized_user_id,
        "items": cart["items"],
        "subtotal": subtotal,
        "discount_applied": discount_code.strip().upper() if (discount_code and discount_code.strip() and discount_code.strip().lower() not in ("none", "null", "undefined")) else None,
        "discount_amount": discount_amount,
        "total": total,
        "status": "processed",
    }

    # Save to mock DB and update cart status
    ORDERS_DB[order_id] = order_details
    cart["status"] = "completed"

    return {
        "status": "success",
        "message": f"Successfully checked out cart '{normalized_cart_id}' and created order '{order_id}'.",
        "order": order_details,
    }

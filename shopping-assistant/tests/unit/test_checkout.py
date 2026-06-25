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

import pytest
from app.tools import CARTS_DB, ORDERS_DB, REDEEMED_CODES, process_cart_checkout


@pytest.fixture(autouse=True)
def reset_db():
    # Save original state
    original_carts = {
        "cart_123": {
            "user_id": "user_123",
            "items": [
                {
                    "name": "Premium Wireless Headphones",
                    "price": 150.0,
                    "quantity": 1,
                }
            ],
            "status": "active",
        },
        "cart_456": {
            "user_id": "user_456",
            "items": [
                {
                    "name": "Ergonomic Office Chair",
                    "price": 300.0,
                    "quantity": 1,
                },
                {"name": "Desk Mat", "price": 25.0, "quantity": 2},
            ],
            "status": "active",
        },
        "guest_cart_789": {
            "user_id": "guest_789",
            "items": [{"name": "USB-C Cable", "price": 15.0, "quantity": 3}],
            "status": "active",
        },
    }

    # Reset databases
    CARTS_DB.clear()
    for k, v in original_carts.items():
        CARTS_DB[k] = {
            "user_id": v["user_id"],
            "items": [item.copy() for item in v["items"]],
            "status": v["status"],
        }
    ORDERS_DB.clear()
    REDEEMED_CODES.clear()
    yield


def test_checkout_success() -> None:
    """Test successful checkout without discount."""
    res = process_cart_checkout(cart_id="cart_123", user_id="user_123")
    assert res["status"] == "success"
    assert CARTS_DB["cart_123"]["status"] == "completed"

    order = res["order"]
    assert order["cart_id"] == "cart_123"
    assert order["user_id"] == "user_123"
    assert order["subtotal"] == 150.0
    assert order["discount_amount"] == 0.0
    assert order["total"] == 150.0
    assert order["discount_applied"] is None
    assert order["order_id"] in ORDERS_DB


def test_checkout_with_discount_success() -> None:
    """Test successful checkout with a valid discount code."""
    res = process_cart_checkout(
        cart_id="cart_456", user_id="user_456", discount_code="SUMMER20"
    )
    assert res["status"] == "success"
    assert CARTS_DB["cart_456"]["status"] == "completed"

    order = res["order"]
    assert order["cart_id"] == "cart_456"
    assert order["user_id"] == "user_456"
    assert order["subtotal"] == 350.0  # 300 + 25*2
    assert order["discount_amount"] == 70.0  # 20% of 350
    assert order["total"] == 280.0
    assert order["discount_applied"] == "SUMMER20"
    assert "SUMMER20" in REDEEMED_CODES


def test_checkout_wrong_owner() -> None:
    """Test that checkout is rejected if the user ID does not match the cart owner."""
    res = process_cart_checkout(cart_id="cart_123", user_id="user_456")
    assert res["status"] == "failure"
    assert "Access Denied" in res["message"]
    assert CARTS_DB["cart_123"]["status"] == "active"
    assert len(ORDERS_DB) == 0


def test_checkout_cart_not_found() -> None:
    """Test that checkout is rejected for a non-existent cart."""
    res = process_cart_checkout(cart_id="nonexistent_cart", user_id="user_123")
    assert res["status"] == "failure"
    assert "not found" in res["message"]
    assert len(ORDERS_DB) == 0


def test_checkout_already_completed() -> None:
    """Test that checkout is rejected for an already processed/completed cart."""
    # First checkout
    res = process_cart_checkout(cart_id="cart_123", user_id="user_123")
    assert res["status"] == "success"

    # Second checkout
    res2 = process_cart_checkout(cart_id="cart_123", user_id="user_123")
    assert res2["status"] == "failure"
    assert "cannot be checked out" in res2["message"]


def test_checkout_guest_discount_denied() -> None:
    """Test that guest users are denied from using discount codes."""
    res = process_cart_checkout(
        cart_id="guest_cart_789", user_id="guest_789", discount_code="WELCOME50"
    )
    assert res["status"] == "failure"
    assert "registered user ID is required" in res["message"]
    assert CARTS_DB["guest_cart_789"]["status"] == "active"
    assert len(ORDERS_DB) == 0


def test_checkout_invalid_discount_denied() -> None:
    """Test that checkout fails if the discount code is invalid."""
    res = process_cart_checkout(
        cart_id="cart_123", user_id="user_123", discount_code="INVALID_CODE"
    )
    assert res["status"] == "failure"
    assert "invalid" in res["message"]
    assert CARTS_DB["cart_123"]["status"] == "active"
    assert len(ORDERS_DB) == 0


def test_checkout_double_discount_redemption_denied() -> None:
    """Test that a discount code cannot be redeemed twice across multiple checkouts."""
    # First checkout redeems WELCOME50
    res = process_cart_checkout(
        cart_id="cart_123", user_id="user_123", discount_code="WELCOME50"
    )
    assert res["status"] == "success"

    # Second checkout attempts to redeem WELCOME50 again for user_456
    res2 = process_cart_checkout(
        cart_id="cart_456", user_id="user_456", discount_code="WELCOME50"
    )
    assert res2["status"] == "failure"
    assert "already been redeemed" in res2["message"]
    assert CARTS_DB["cart_456"]["status"] == "active"

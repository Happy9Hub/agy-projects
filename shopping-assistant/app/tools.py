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

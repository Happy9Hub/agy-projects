# Copyright (c) 2026 MyCompany LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib.request
import urllib.parse

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

def login():
    """Default login placeholder."""
    pass

def login_with_google(auth_code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict:
    """
    Exchanges a Google OAuth2 authorization code for user information.
    
    Args:
        auth_code: The authorization code received from the Google OAuth consent flow.
        client_id: Your Google OAuth2 client ID.
        client_secret: Your Google OAuth2 client secret.
        redirect_uri: The redirect URI registered with Google.
        
    Returns:
        A dictionary containing user info (e.g., email, name) or an error dictionary.
    """
    # 1. Prepare token exchange payload
    data = urllib.parse.urlencode({
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }).encode("utf-8")
    
    try:
        # 2. Exchange authorization code for tokens
        req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data, method="POST")
        with urllib.request.urlopen(req) as response:
            token_response = json.loads(response.read().decode())
            
        access_token = token_response.get("access_token")
        if not access_token:
            return {"error": "Failed to retrieve access token from Google."}
            
        # 3. Retrieve user profile information using the access token
        userinfo_req = urllib.request.Request(GOOGLE_USERINFO_URL)
        userinfo_req.add_header("Authorization", f"Bearer {access_token}")
        
        with urllib.request.urlopen(userinfo_req) as userinfo_response:
            user_profile = json.loads(userinfo_response.read().decode())
            
        return {
            "success": True,
            "user_info": user_profile
        }
        
    except urllib.error.HTTPError as e:
        try:
            error_details = json.loads(e.read().decode())
        except Exception:
            error_details = e.reason
        return {"error": f"HTTP Error during login: {error_details}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

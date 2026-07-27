import os
import requests
from dotenv import load_dotenv
load_dotenv()

API_URL = "http://localhost:8000/hashes" #fill this in later!!! It's a base URL.
# Basically, the FastAPI server will now need to process different requests based on the HTTP method, not just name of the endpoint.
password = os.getenv("ServerPassword")

def add_new_school_or_delegates_to_existing_school_and_request_hashes(finalassignments: dict[str, list]) -> dict[str, str]:
    """
    Sends finalassignments data to the FastAPI endpoint and returns a dictionary
    mapping school identifiers to generated user hashes.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. accept a JSON payload with the finalassignments dictionary. Read into the string of that dictionary to see if the school name is already in database, to discern if adding new delegate or adding another school.
    3. return a dictionary, where there is a key value pair with key being "data", and value being a dictionary with the hashes {"school - #1": "hash12345", ...}
    4. return appropriate HTTP status codes for errors (401, 403, 422, 500, etc.)
    5. return an optional message with things like "school already in database", or "new school".
    """
    # 1. Prepare headers
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    try:
            # Send POST request with a timeout (e.g., 5 seconds)
            response = requests.post(
                API_URL, 
                json=finalassignments, 
                headers=headers,
                timeout=5
            )
            
            # Check specific HTTP status codes returned by the server
            if response.status_code == 401 or response.status_code == 403:
                print("Error: Wrong password or unauthorized access.")
                return {}
                
            elif response.status_code == 422 or response.status_code == 400:
                print("Error: Data error. The sent assignments dictionary formatted incorrectly.")
                return {}
                
            elif response.status_code >= 500:
                print("Error: Internal server error on the FastAPI server.")
                return {}

            # Fallback to catch any other non-200 HTTP status code
            response.raise_for_status()
            
            # Parse successful JSON payload
            payload = response.json()
            hashes: dict[str, str] = payload.get("data", {})
            server_message = payload.get("message", "")
            if server_message:
                print(f"Message from server: {server_message}")
            return hashes

    # Network-level exceptions (Server unreachable or timed out)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return {}
        
    # Generic catch-all for any other unexpected requests issues
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return {}

def drop_delegates_from_school_and_delete_hashes(delegates_to_drop: dict[str, list]) -> dict[str, str]:
    """
    Sends delegates_to_drop to FastAPI to remove delegates and return their deleted hashes.
    Prints any descriptive messages sent back by the server.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. accept a JSON payload with the delegates_to_drop dictionary. Check if that delegate exists in the database, and if so, delete them and their hashes. Do not delete at all if even a single delegate doesn't exist.
    3. return a dictionary, where there is a key value pair with key being "data", and value being a dictionary with the hashes deleted {"school - #1": "hash12345", ...}
    4. return appropriate HTTP status codes (200, 401, 403, 400, 422, 500, etc.)
    5. return an optional message with things like "delegate does not exist".
    """
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    try:
        # Send DELETE request with delegates payload
        response = requests.delete(
            API_URL, 
            json=delegates_to_drop, 
            headers=headers,
            timeout=5
        )
        
        # Check specific HTTP status codes
        if response.status_code in (401, 403):
            print("Error: Wrong password or unauthorized access.")
            return {}
            
        elif response.status_code in (400, 422):
            print("Error: Data error. The delegates dictionary is formatted incorrectly.")
            return {}
            
        elif response.status_code >= 500:
            print("Error: Internal server error on the FastAPI server.")
            return {}

        response.raise_for_status()
        
        # Parse response JSON
        payload = response.json()
        
        # Print server message if provided
        if "message" in payload and payload["message"]:
            print(f"Server Message: {payload['message']}")
            
        # Extract and return deleted hashes mapping
        deleted_hashes: dict[str, str] = payload.get("data", {})
        return deleted_hashes

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return {}
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return {}

def request_hashes_for_school(school_name: str) -> dict[str, str]:
    """
    Fetches the hashes mapping for a specific school from the FastAPI server.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. accept a query parameter with the school name
    3. return a dictionary, where there is a key value pair with key being "data", and value being a dictionary with the hashes {"school - #1": "hash12345", ...}
    4. return appropriate HTTP status codes (200, 401, 403, 400, 422, 500, etc.)
    5. return an optional message with things like "School not found".
    """
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    # Query parameter sent in the URL string
    params = {
        "school_name": school_name
    }
    
    try:
        # Sends GET request to API_URL
        response = requests.get(
            API_URL, 
            params=params, 
            headers=headers,
            timeout=5
        )
        
        # Specific HTTP status code handling
        if response.status_code in (401, 403):
            print("Error: Wrong password or unauthorized access.")
            return {}
            
        elif response.status_code in (400, 422):
            print(f"Error: Invalid query parameter or school name '{school_name}'.")
            return {}
            
        elif response.status_code == 404:
            print(f"Error: School '{school_name}' was not found.")
            return {}
            
        elif response.status_code >= 500:
            print("Error: Internal server error on the FastAPI server.")
            return {}

        response.raise_for_status()
        
        payload = response.json()
        
        # Print optional message from the server if present
        if "message" in payload and payload["message"]:
            print(f"Server Message: {payload['message']}")
            
        hashes: dict[str, str] = payload.get("data", {})
        return hashes

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return {}
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return {}

def request_all_awards_data() -> dict[tuple[str, str], str]:
    """
    Fetches all award data from FastAPI and formats it into a dictionary 
    where keys are (country, committee) tuples and values are award names.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. Be located on the /awards endpoint.
    3. return a list with each item being a dictionary with keys "country", "committee", and "award".
    4. return appropriate HTTP status codes (200, 401, 403, 400, 422, 500, etc.)
    5. return an optional message with things like "X committee(s) don't have awards yet".
    """
    API_URL = "http://127.0.0.1:8000/awards"
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    try:
        # GET request to fetch awards data
        response = requests.get(
            API_URL, 
            headers=headers,
            timeout=5
        )
        
        # Status code checks
        if response.status_code in (401, 403):
            print("Error: Wrong password or unauthorized access.")
            return {}
            
        elif response.status_code >= 500:
            print("Error: Internal server error on the FastAPI server.")
            return {}

        response.raise_for_status()
        
        payload = response.json()
        
        # Print optional server message if included
        if "message" in payload and payload["message"]:
            print(f"Server Message: {payload['message']}")
            
        # Parse list of items from 'data' and construct tuple-keyed dict
        # Expecting 'data' to be a list of objects like:
        # [{"country": "USA", "committee": "DISEC", "award": "Best Delegate"}, ...]
        raw_awards_list = payload.get("data", [])

        return raw_awards_list

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return {}
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return {}

def regenerate_hashes_for_delegate(committee: str, country: str) -> str:
    """
    Triggers a hash regeneration on the server for a specific delegate 
    and returns the new hash string.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. Be located on the /hashes/regenerate/delegate endpoint.
    3. Expect country and committee as query parameters.
    4. return appropriate HTTP status codes (200, 401, 403, 400, 422, 500, etc.)
    5. return an optional message with things like "Delegate does not exist".
    6. Return a JSON payload with a single key "data" and value being the new hash string.
    """

    API_URL = "http://127.0.0.1:8000/hashes/regenerate/delegate"
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    # Send committee and country as query params
    params = {
        "committee": committee,
        "country": country
    }
    
    try:
        # POST request (without a JSON body, using params instead)
        response = requests.post(
            API_URL, 
            params=params, 
            headers=headers,
            timeout=5
        )
        
        if response.status_code in (401, 403):
            print("Error: Wrong password or unauthorized access.")
            return ""
            
        elif response.status_code == 404:
            print(f"Error: Delegate ({country}, {committee}) not found.")
            return ""
            
        elif response.status_code >= 500:
            print("Error: Internal server error on the FastAPI server.")
            return ""

        response.raise_for_status()
        
        payload = response.json()
        
        if "message" in payload and payload["message"]:
            print(f"Server Message: {payload['message']}")
            
        # Extract the single new hash string from the payload
        # Expecting server JSON: {"data": "new_generated_hash_123"}
        new_hash: str = payload.get("data", "")
        return new_hash

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return ""
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return ""

def regenerate_hashes_for_school(school_name: str) -> dict[str, str]:
    """
    Triggers a bulk hash regeneration for an entire school 
    and returns a dictionary mapping delegate keys to their new hashes.

    Matching FastAPI function should: 
    1. accept bearer header token.
    2. Be located on the /hashes/regenerate/school endpoint.
    3. Expect school name as a query parameter.
    4. return appropriate HTTP status codes (200, 401, 403, 400, 422, 500, etc.)
    5. return an optional message with things like "School does not exist" or "Hash regeneration error".
    6. Return a JSON payload with a single key "data" and value being a dictionary of new hashes for all delegates in that school.
    """

    API_URL = "http://127.0.0.1:8000/hashes/regenerate/school"
    headers = {
        "Authorization": f"Bearer {password}",
        "Content-Type": "application/json"
    }
    
    # Send school_name as a query parameter
    params = {
        "school_name": school_name
    }
    
    try:
        # POST request to trigger the bulk regeneration
        response = requests.post(
            API_URL, 
            params=params, 
            headers=headers,
            timeout=5
        )
        
        # Handle specific HTTP status codes
        if response.status_code in (401, 403):
            print("Error: Wrong password or unauthorized access.")
            return {}
            
        elif response.status_code == 404:
            print(f"Error: School '{school_name}' was not found.")
            return {}
            
        elif response.status_code in (400, 422):
            print(f"Error: Invalid parameters for school name '{school_name}'.")
            return {}
            
        elif response.status_code >= 500:
            print("Error: Internal server error on the FastAPI server.")
            return {}

        response.raise_for_status()
        
        payload = response.json()
        
        # Print optional server message if present
        if "message" in payload and payload["message"]:
            print(f"Server Message: {payload['message']}")
            
        # Parse updated hashes dictionary from response payload
        new_hashes: dict[str, str] = payload.get("data", {})
        return new_hashes

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print("Error: No server response. Check if FastAPI is running and accessible.")
        return {}
        
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with server: {e}")
        return {}
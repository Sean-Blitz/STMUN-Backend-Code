import requests
import json
import datetime

def search_records(rID):
    url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/tblnLy4pZDVjGskAw/{rID}" #change this next year.
    auth_token = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    resp=requests.get(url,headers=headers)
    d1 = str(resp.json())
    d2 = d1.replace("\'", "\"").replace("True", "true").replace("False", "false").replace("Null", "null")
    #getting rid of the stupid JSON errors Airtable has
    response = json.loads(d2)

    fields = response["fields"]
    #fields is a dictionary

    sName = fields["School Name"]
    sAddress = fields["School Address"]
    sPhoneNumber = fields["School Phone Number"]
    aName = fields["Advisor Name"]
    aPhoneNumber = fields["Advisor Phone Number"]
    aEmail = fields["Advisor Email"]
    DelegateCount = fields["Number of Delegates(Initial)"]
    Balance = fields["Balance (from Finance (WIP) 2)"]
    Balance = int(Balance[0])
    CheckDelegateCount = fields["Number of Delegates (Final) (from Finance (WIP) 2)"]
    CheckDelegateCount = int(CheckDelegateCount[0])
    Subtotal = fields["Subtotal (from Finance (WIP) 2)"]
    Subtotal = int(Subtotal[0])
    DelFee = fields["Delegation Fee (from Finance (WIP) 2)"]
    DelFee = int(DelFee[0])

    return sName, sAddress, sPhoneNumber, aName, aPhoneNumber, aEmail, DelegateCount, Balance, CheckDelegateCount, Subtotal, DelFee

def search_formResponse(rID):
    url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/tbl7XkJTdmk2kIowi/{rID}" #change this next year.
    auth_token = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    resp=requests.get(url,headers=headers)
    d1 = str(resp.json())
    d2 = d1.replace("\'", "\"").replace("True", "true").replace("False", "false").replace("Null", "null")
    #getting rid of the stupid JSON errors Airtable has
    response = json.loads(d2)

    fields = response["fields"]
    #fields is a dictionary

    city = fields["City"]
    state = fields["State"]
    zip_code = fields["Zip Code"]
    DelCount = fields["Number of Delegates(Initial)"]

    return city, state, zip_code, DelCount

def get_latest_record_id(api_token, base_id, table_name):
    """
    Returns the record ID of the most recently created record in an Airtable table.

    Args:
        api_token (str): Airtable API token
        base_id (str): Airtable base ID
        table_name (str): Table name

    Returns:
        str or None: Record ID, or None if table is empty
    """
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    params = {
        "sort[0][field]": "Created Time",
        "sort[0][direction]": "desc",
        "maxRecords": 1
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    records = response.json().get("records", [])

    if not records:
        return None

    return records[0]["id"]

def view_latest_record(rID):
    url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/tblnLy4pZDVjGskAw/{rID}" #change this next year.
    auth_token = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"

    headers = {
        "Authorization": f"Bearer {auth_token}"
    }
    resp=requests.get(url,headers=headers)
    d1 = str(resp.json())
    d2 = d1.replace("\'", "\"").replace("True", "true").replace("False", "false").replace("Null", "null")
    #getting rid of the stupid JSON errors Airtable has
    response = json.loads(d2)

    fields = response["fields"]
    #fields is a dictionary

    sName = fields["School Name"]
    sAddress = fields["School Address"]
    aPhoneNumber = fields["Advisor Phone Number"]
    aEmail = fields["Advisor Email"]
    DelegateCount = fields["Number of Delegates(Initial)"]
    timestamp = fields["Timestamp"]
    date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").date()
    datestr = str(date.month)+"/"+str(date.day)+"/"+str(date.year)

    print(sName + "\n" + sAddress + "\n" + aPhoneNumber + "\n" + aEmail + "\nNumber of delegates: " + str(DelegateCount) + "\n" + datestr)
    return sName, sAddress, aPhoneNumber, aEmail, DelegateCount, date, datestr

def create_airtable_record(record_id_value, date_1, DateBox, DelBox, NumDelegates, number_2, schoolName):
    """
    Updates a single Airtable record with fixed fields.

    Args:
        api_token (str): Airtable personal access token
        airtable_record_id (str): Airtable record ID to update
        record_id_value (str): Value for Record ID field
        date_1 (str): ISO date (YYYY-MM-DD)
        date_2 (str): ISO date (YYYY-MM-DD)
        number_1 (int or float)
        number_2 (int or float)
    """
    url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/tblnLy4pZDVjGskAw" #change this next year.
    api_token = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    NumDelegates = str(NumDelegates)
    payload = {
        "fields": {
            "All Info": [record_id_value],
            "Form Response 2": [record_id_value],
            "Registration Date": date_1,
            "Name": schoolName,
            DateBox: date_1,
            DelBox: NumDelegates,
            "Delegation Fee": number_2
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("Status code:", response.status_code)
    print("Response text:", response.text)

    if response.status_code != 200:
        try:
            print("Response JSON:", response.json())
        except Exception:
            pass

    response.raise_for_status()

    return response.json()

def get_field_by_name(search_name, search_column):
    """
    Searches Airtable table for a value and returns another field from the same row.

    Args:
        table_id (str): Airtable table ID (or full URL path after app ID)
        api_key (str): Airtable API key
        search_name (str): Value to search for in the column
        search_column (str): Column to search in
        return_column (str): Column to retrieve from the matching row

    Returns:
        str or None: Value from return_column in the matching row
    """
    api_key = "patcikx9vfYeXF4gz.20004c29f9f7601a7bb9ee1d4474468dc46e4c4a1ebcc1105b7fd6a310933560"
    return_column = "Record ID"
    url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/tbl7XkJTdmk2kIowi" #change this next year.
    headers = {"Authorization": f"Bearer {api_key}"}

    formula = f"{{{search_column}}}='{search_name}'"

    response = requests.get(url, headers=headers, params={"filterByFormula": formula})
    response.raise_for_status()

    data = response.json().get("records", [])

    if not data:
        return None

    # Assume only one matching record
    record = data[0]["fields"]
    return record.get(return_column)

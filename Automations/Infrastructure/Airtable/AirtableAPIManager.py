import requests
import json
import datetime
import os
from dotenv import load_dotenv
load_dotenv()

finance_table_id = os.getenv("FINANCE_TABLE_ID")  # Ensure this is set in your .env file
form_response_table_id = os.getenv("FORM_RESPONSE_TABLE_ID")  # Ensure this is set in your .env file
class AirtableAPI:
    def __init__(self):
        self.api_token = os.getenv("API_KEY")

    def search_records(self, record_id):
        headers = {"Authorization": f"Bearer {self.api_token}"}

        # 1. Fetch main record (Schools/Advisors table)
        school_url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{form_response_table_id}/{record_id}"
        school_resp = requests.get(school_url, headers=headers)
        school_data = school_resp.json()  # requests.json() converts JSON directly to Python dict

        fields = school_data.get("fields", {})

        sName = fields.get("School Name")
        sAddress = fields.get("School Address")
        sPhoneNumber = fields.get("School Phone Number")
        aName = fields.get("Advisor Name")
        aPhoneNumber = fields.get("Advisor Phone Number")
        aEmail = fields.get("Advisor Email")
        head_delegate_email = fields.get("Head Delegate Email")
        DelegateCount = fields.get("Number of Delegates (Initial)")
        finance_record_id = fields.get("Finance (Linked)")
        finance_record_id = finance_record_id[0] if finance_record_id else None  # Get the first linked record ID

        # 2. Fetch record from the second (Finance) table
        finance_url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{finance_table_id}/{finance_record_id}"
        finance_resp = requests.get(finance_url, headers=headers)
        finance_data = finance_resp.json()

        fin_fields = finance_data.get("fields", {})

        # Extract finance fields directly from the second table
        # Using .get() prevents KeyError if a field is empty/missing
        Balance = int(fin_fields.get("Balance", 0))
        CheckDelegateCount = int(
            fin_fields.get("Number of Delegates (Final)", 0)
        )
        Subtotal = int(fin_fields.get("Subtotal", 0))
        DelFee = int(fin_fields.get("Delegation Fee", 0))

        return sName, sAddress, sPhoneNumber, aName, aPhoneNumber, aEmail, DelegateCount, Balance, CheckDelegateCount, Subtotal, DelFee, head_delegate_email

    def search_formResponse(self, rID):
        url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{form_response_table_id}/{rID}" #change this next year.
        auth_token = self.api_token

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
        DelCount = fields["Number of Delegates (Initial)"]

        return city, state, zip_code, DelCount

    def get_latest_record_id(self, base_id, table_name):
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
            "Authorization": f"Bearer {self.api_token}"
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

    def view_latest_record(self, rID):
        url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{form_response_table_id}/{rID}" #change this next year.
        auth_token = self.api_token

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
        DelegateCount = fields["Number of Delegates (Initial)"]
        timestamp = fields["Timestamp"]
        date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ").date()
        datestr = str(date.month)+"/"+str(date.day)+"/"+str(date.year)

        print(sName + "\n" + sAddress + "\n" + aPhoneNumber + "\n" + aEmail + "\nNumber of delegates: " + str(DelegateCount) + "\n" + datestr)
        return sName, sAddress, aPhoneNumber, aEmail, DelegateCount, date, datestr

    def create_airtable_record(self, record_id_value, date_1, DateBox, DelBox, NumDelegates, number_2, schoolName):
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
        url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{form_response_table_id}" #change this next year.
        api_token = self.api_token
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

    def get_field_by_name(self, search_name, search_column):
        """
        Searches Airtable table for a value and returns another field from the same row.

        Args:
            search_name (str): Value to search for in the column
            search_column (str): Column to search in
            return_column (str): Column to retrieve from the matching row

        Returns:
            str or None: Value from return_column in the matching row
        """
        api_key = self.api_token
        return_column = "Record ID"
        url = f"https://api.airtable.com/v0/appEySB2x9jqHy16Q/{form_response_table_id}" #change this next year.
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

    def select_dropdown_option_raw(
        self,
        base_id: str,
        table_name: str,
        record_id: str,
        field_name: str,
        target_option: str,
    ) -> bool:
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        payload = {"fields": {field_name: target_option}, "typecast": False}

        response = requests.patch(url, headers=headers, json=payload)

        if response.status_code == 200:
            return True

        # 422 indicates invalid dropdown selection or schema mismatch
        if response.status_code == 422:
            error_details = response.json().get("error", {})
            print(
                f"[Airtable 422] Option '{target_option}' rejected for field '{field_name}'. Details: {error_details}"
            )
        else:
            print(f"[Airtable Error] HTTP {response.status_code}: {response.text}")

        return False

    def find_airtable_record_id(self, base_id: str, table_name: str, school_name: str, delegate_num: str):
        """
        Searches the Airtable table using the REST API for a record matching
        'School Name' and 'Delegate #'.
        """
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        headers = {
            "Authorization": f"Bearer {self.api_token}"
        }
        
        # Airtable filter formula
        formula = f"AND({{School Name}} = '{school_name}', {{Delegate #}} = '{delegate_num}')"
        params = {
            "filterByFormula": formula
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            records = response.json().get("records", [])
            if records:
                return records[0]["id"]
        else:
            print(f"Error searching Airtable: {response.status_code} - {response.text}")
            
        return None

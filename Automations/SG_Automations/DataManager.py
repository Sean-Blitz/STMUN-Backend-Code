from Entrypoint import Display
import sys

class SchoolDelegates:
    def __init__(self):
        self.committee: list[str] = []
        self.committee_type: list[str] = []
        self.country: list[str] = []

    def add_delegate(self, committee, committee_type, country):
        self.committee.append(committee)
        self.committee_type.append(committee_type)
        self.country.append(country)

class SchoolInformation:
    def __init__(self):
        self.advisor: str
        self.advisor_email: str
        self.head_del_email: str
        self.schoolname: str
        self.country_preferences: list[str]
        self.region_bloc: str
        self.security_council_preference: bool
        self.numdels: int

    def add_school(self, advisor, advisor_email, head_del_email, schoolname, 
                   country_preferences, region_bloc, security_council_preference, numdels):
        pass

class ConferenceInformation:
    def __init__(self, available_countries):
        self.committee_names: list = []
        self.available_countries: list[str] = available_countries
        self.single_committee_names: list[str] = []
        self.committee_types: list[str] = []
        self.committee_percentage_filled: list[float] = []
        self.committee_spots = []
        self.needing_suggestions_committee_names: list[str] = []

    def add_committee(self, committee_name: str, spots: int, percentage_filled: float,
                      type="GA", single_committee=False, need_suggestion = False):
        if committee_name not in self.committee_names:
            self.committee_names.append(committee_name)
            self.committee_spots.append(spots)
            self.committee_percentage_filled.append(percentage_filled)
            self.committee_types.append(type)
        else:
            raise ValueError(f"Committee name {committee_name} is not unique. Ensure that names in sheets are not repeated.")
        
        if single_committee is True:
            self.single_committee_names.append(committee_name)
        if need_suggestion is True:
            self.needing_suggestions_committee_names.append(committee_name)

    def get_committee_percentage(self, committee_name):
        return self.committee_percentage_filled[self.committee_names.index(committee_name)]

    def get_committee_double_status(self, committee_name):
        if committee_name in self.single_committee_names:
            return False
        else:
            return True

    def get_committee_type(self, committee_name):
        return self.committee_types[self.committee_names.index(committee_name)]
class SchoolDelegates:
    def __init__(self):
        self.number: list[int] = []
        self.committee: dict[int, str] = {}
        self.committee_type: dict[int, str] = {}
        self.country: dict[int, str] = {}
        self.suggestions: dict[int, list[str]] = {}
        self.preferences_in_committee: dict[int, list[str]] = {}

    def add_delegate(self, committee, committee_type, country, number):
        self.number.append(number)
        if number in self.number:
            raise ValueError(f"Delegate number {number} is not unique. Ensure that numbers in sheets are not repeated.")
        self.committee[number] = committee
        self.committee_type[number] = committee_type
        self.country[number] = country

    def add_delegate_suggestion(self, number, suggestions_list, preferences_in_committee_list):
        if number not in self.number:
            raise ValueError(f"Delegate number {number} does not exist. Ensure that the delegate has been added before adding suggestions.")
        self.suggestions[number] = suggestions_list
        self.preferences_in_committee[number] = preferences_in_committee_list

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
        GA_count: int
        Spec_count: int
        Crisis_count: int

    def add_school(self, advisor_email, head_del_email, schoolname, 
                   country_preferences, region_bloc, security_council_preference, numdels):
        self.advisor_email = advisor_email
        self.head_del_email = head_del_email
        self.schoolname = schoolname
        self.country_preferences = country_preferences
        self.region_bloc = region_bloc
        self.security_council_preference = security_council_preference
        self.numdels = numdels

    def set_assignment_counts(self, GA_count, Spec_count, Crisis_count):
        self.GA_count = GA_count
        self.Spec_count = Spec_count
        self.Crisis_count = Crisis_count
        if GA_count + Spec_count + Crisis_count != self.numdels:
            raise ValueError("The sum of GA, Specialized, and Crisis counts does not match the total number of delegates.")

class ConferenceInformation:
    def __init__(self):
        self.committee_names: list = []
        self.available_countries: list[list[str]]
        self.committee_double_status: dict[str, bool] = {}
        self.committee_types: dict[str, str] = {}
        self.committee_percentage_filled: dict[str, float] = {}
        self.committee_spots: dict[str, int] = {}
        self.needing_suggestions_committee_names: list[str] = []
        self.ranges: dict[str, str] = {}
        self.backup: dict[str, str] = {}

    def add_committee(self, committee_name: str, spots: int, percentage_filled: float, range,
                      type="GA", single_committee=False, need_suggestion = False):
        if committee_name not in self.committee_names:
            self.committee_names.append(committee_name)
            self.committee_spots[committee_name] = spots
            self.committee_percentage_filled[committee_name] = percentage_filled
            self.committee_types[committee_name] = type
            self.ranges[committee_name] = range
        else:
            raise ValueError(f"Committee name {committee_name} is not unique. Ensure that names in sheets are not repeated.")
        self.committee_double_status[committee_name] = not single_committee

        if need_suggestion is True:
            self.needing_suggestions_committee_names.append(committee_name)

    def get_lowest_committee_percentage_for_type(self, committee_type):
        names = [name for name in self.committee_names if self.committee_types[name] == committee_type]
        lowest_percentage_index = min(names, key=lambda x: self.committee_percentage_filled[x])
        return self.committee_names[lowest_percentage_index]

    def add_available_assignments(self, available_countries):
        self.available_countries = available_countries

    def add_backup(self, backup):
        self.backup = backup

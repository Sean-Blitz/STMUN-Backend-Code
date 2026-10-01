import os
import sys
import random
from collections import Counter
from dotenv import load_dotenv
from Infrastructure import DisplayClass
from SG_Automations.Assignments_Sheets_Adapter import Assignments_to_Sheets
from DataManager import SchoolDelegates, SchoolInformation, ConferenceInformation

load_dotenv()
Display = DisplayClass()
SheetsAPI = Assignments_to_Sheets()

top5 = {"China", "United States", "Russia", "United Kingdom", "France"}

def generate_dictionary_of_suggestions(SchoolInfo: SchoolInformation, Delegates: SchoolDelegates, ConferenceInfo: ConferenceInformation) -> dict[str, list[str]] | None:
    """
    Generates up to 5 suggested available countries for each delegate in a GA committee,
    weighted by the school's historical award tier.
    
    finalassignments format: {"School - #": ["committee", "type", "country"]}
    availableCountries format: [["committee", "country_name"], ...]
    preferences format: ["country1", "country2", ...]
    Returns: countrySuggestionsDictionary, which is {"School - #": ["Country 1", "Country 2", ...]}

    Generate suggestions based on school size, awards_history, and trust status. Do it only for GAs, for now.
    You will need to find all the countries you currently have, and group them into difficulty groups (3 groups).
    Big countries should be in their own separate group, and only select from this for big reputable schools.
    The code selects a certain few countries from each, with how much from each based on school's status.
    With those selected few, you search the availableCountries by committee (the committee for that delegate), and if that country is available, add it to the suggestions.

    You don't actually have to account for double delegates, because they are binded together later during assignments anyways.
    """
    tier1 = {"Canada","Argentina","Australia","Denmark","Finland","Germany","Netherlands","Norway","Spain","Sweden","Switzerland","Portugal",
             "Republic of Korea","Turkey","Italy","Mexico","India","Hungary","Japan","Belgium","Austria","Pakistan","Morocco","Brazil","Singapore",
            "Egypt","Saudi Arabia","Poland"}
    tier2 = {"Cote d'Ivoire", "Croatia","Colombia","Chile","New Zealand","Vietnam","Thailand","Venezuela","U.A.E.","Ukraine","Ireland","Greece",
            "Iraq","Kazakhstan","Senegal","Czech Rep.","Dominican Republic","Algeria","Bangladesh","Cambodia","Iceland","Indonesia","Kenya","Malaysia",
            "Lebanon","Luxembourg","Haiti","Paraguay","Panama","Nigeria","Myanmar","Mongolia","Ethiopia","Estonia","Bulgaria","D.R.C.","Qatar","Ecuador",
            "Uruguay","D.P.R.K.","Iran","Israel","Cuba","Costa Rica","Philippines","Lithuania"}

    blacklist = os.getenv("BLACKLIST")
    if blacklist is not None:
        blacklist = [school.strip() for school in blacklist.lower().split(",") if school.strip()]
    else:
        Display.display("No schools in the blacklist")
        blacklist = []
    sanitized_school_name = SchoolInfo.schoolname.lower().replace("high", "").replace("school", "").replace("hs", "").replace("college", "").replace("preparatory", "").replace("prep", "").strip()
    school_status = SheetsAPI.get_school_awards_data(sanitized_school_name) # returns "good", "great", "below average", or "unexperienced"

    if SchoolInfo.numdels >= 30 and sanitized_school_name not in blacklist:
        count = 0
        for committee in ConferenceInfo.committee_names:
            if committee in ConferenceInfo.needing_suggestions_committee_names:
                count = count +1
        half1 = count//2 
        suggest_p5_countries(top5, half1, SchoolInfo, ConferenceInfo, Delegates)
        suggest_countries_based_on_ranking(school_status, tier1, tier2, SchoolInfo, ConferenceInfo, Delegates)

    elif SchoolInfo.numdels < 30 and sanitized_school_name not in blacklist:
        suggest_countries_based_on_ranking(school_status, tier1, tier2, SchoolInfo, ConferenceInfo, Delegates)

    elif sanitized_school_name in blacklist:
        suggest_countries_for_blacklisted_school(tier1, tier2, SchoolInfo, ConferenceInfo, Delegates)

def suggest_countries_based_on_ranking(school_status, tier1, tier2, SchoolInfo: SchoolInformation, ConferenceInfo: ConferenceInformation, Delegates: SchoolDelegates):
    """
    Keep track of countries already suggested. If suggested more than 4 times in the list, do not suggest that country again.

    Go through each delegate and allocate countries randomly based on status, then committee availability, then country preferences

    Country preferences of the school is selected manually. Interface simply prints the country preferences available in this committee.

    There is a careful dictionary linking logic inside of here that ensures the variables in the dictionary and the loop get updated when needed for ignoring countries.
    """

    if school_status == "great":
        distribution = (0, 3, 3) # take 2 from tier 1, 3 from tier 2, and 4 from tier 3
    elif school_status == "good":
        distribution = (1, 2, 3)
    elif school_status == "below average":
        distribution = (2, 3, 1)
    elif school_status == "unexperienced":
        distribution = (3, 2, 0)
    else:
        Display.display("")
        sys.exit(1)

    generate_suggestions_for_delegates(tier1, tier2, distribution, SchoolInfo, ConferenceInfo, Delegates)

def suggest_p5_countries(top5, half1, SchoolInfo: SchoolInformation, ConferenceInfo: ConferenceInformation, Delegates: SchoolDelegates):
    # do not take into account preferences. Since there are only 5 top countries anyways, just give them random selections.

    preferences = SchoolInfo.country_preferences
    availableCountries = ConferenceInfo.available_countries
    committees_wanting_suggestions = ConferenceInfo.needing_suggestions_committee_names

    for index, (delegate_key, committee) in enumerate(zip(Delegates.number, Delegates.committee.values())):

        if index == half1 or index > half1: # once we get this number of delegates, we stop.
            break
        # Only process General Assembly (GA) committees
        if committee not in committees_wanting_suggestions:
            continue

        # 1. Filter available countries specifically for this delegate's committee, based on if in top5 and if in preferences in committee.
        top5 = {country.strip().lower() for country in top5}
        top5_available_for_comm = [country.strip() for comm, country in availableCountries if comm.strip().lower() == committee.lower() and country.strip().lower() in top5]
        preferences_in_committee = [country for country in top5_available_for_comm if country in preferences]

        Delegates.add_delegate_suggestion(delegate_key, top5_available_for_comm, preferences_in_committee)

def suggest_countries_for_blacklisted_school(tier1, tier2, SchoolInfo, ConferenceInfo, Delegates):
    distribution = (0, 3, 3)
    generate_suggestions_for_delegates(tier1, tier2, distribution, SchoolInfo, ConferenceInfo, Delegates)

def generate_suggestions_for_delegates(tier1, tier2, distribution, SchoolInfo: SchoolInformation, ConferenceInfo: ConferenceInformation, Delegates: SchoolDelegates):
    preferences = SchoolInfo.country_preferences
    availableCountries = ConferenceInfo.available_countries
    committees_wanting_suggestions = ConferenceInfo.needing_suggestions_committee_names
    ignored_countries = []
    already_suggested_countries = []

    for number, committee in Delegates.committee.items():
        preferences_in_committee = set()
        
        # Only process General Assembly (GA) committees
        if committee not in committees_wanting_suggestions:
            continue

        # 1. Filter available countries specifically for this delegate's committee
        available_for_comm = [country.strip() for comm, country in availableCountries if comm.strip().lower() == committee.lower()]

        unique_available_tier1 = list(set([country for country in available_for_comm if country in tier1]))
        unique_available_tier2 = list(set([country for country in available_for_comm if country in tier2]))
        unique_available_tier3 = list(set([country for country in available_for_comm if country not in tier1 and country not in tier2 and country not in top5]))
        assigned_number_of_times = Counter(already_suggested_countries) # counter is a function that counts how many times each country has been suggested already.
        for repeated_country, repeats in assigned_number_of_times.items():
            if repeats == 4 and repeated_country not in ignored_countries:
                if repeated_country in unique_available_tier1:
                    unique_available_tier1 = [name for name in unique_available_tier1 if name != repeated_country]
                if repeated_country in unique_available_tier2:
                    unique_available_tier2 = [name for name in unique_available_tier2 if name != repeated_country]
                if repeated_country in unique_available_tier3:
                    unique_available_tier3 = [name for name in unique_available_tier3 if name != repeated_country]
                ignored_countries.append(repeated_country)

        delegate_country_suggestions = []
        # the code segment here picks from the tier lists based on how many to choose from.
        if len(unique_available_tier1) >= distribution[0]:
            suggestions = random.sample(unique_available_tier1, k=distribution[0])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        if len(unique_available_tier2) >= distribution[1]:
            suggestions = random.sample(unique_available_tier2, k=distribution[1])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        if len(unique_available_tier3) >= distribution[2]:
            suggestions = random.sample(unique_available_tier3, k=distribution[2])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        # process preferences that are in the delegate's committee and store in a list. Have the dictionary value
        # for SuggestionsDictionary be a tuple, where first value is the list of suggestions for that delegate, 
        # and second value is the list of preferences available in that committee.
        for preference in preferences:
            if preference in available_for_comm:
                preferences_in_committee.add(preference)
        Delegates.add_delegate_suggestion(number, delegate_country_suggestions, list(preferences_in_committee))
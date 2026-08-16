import os
import sys
import random
from collections import Counter
from dotenv import load_dotenv
from Automations.Infrastructure import DisplayClass
from Assignments_Sheets_Adapter import Assignments_to_Sheets

load_dotenv()
Display = DisplayClass()
SheetsAPI = Assignments_to_Sheets()

def generate_dictionary_of_suggestions(finalassignments: dict, numdels: int, availableCountries: list, schoolname: str, preferences: list[str]) -> dict[str, list[str]] | None:
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
    top5 = {"China", "United States", "Russia", "United Kingdom", "France"}

    blacklist = os.getenv("BLACKLIST")
    blacklist = blacklist.lower().split(",") if blacklist is not None else print("No schools in the blacklist")
    sanitized_school_name = schoolname.lower().replace("high", "").replace("school", "").replace("hs", "").replace("college", "").replace("preparatory", "").replace("prep", "").strip()
    school_status = SheetsAPI.get_school_awards_data(sanitized_school_name) # returns "good", "great", "below average", or "unexperienced"

    if blacklist is not None:
        if numdels >= 30 and sanitized_school_name not in blacklist:
            count = 0
            for delegate_key, (committee, comm_type, country) in finalassignments.items():
                if comm_type.upper() == "GA":
                    count = count +1
            half1 = count//2
            firstcountrySuggestionsDictionary, already_suggested_delegates = suggest_p5_countries(top5, half1, preferences, finalassignments, availableCountries)
            other_half_finalassignments = finalassignments.copy()
            for delegate in already_suggested_delegates:
                del other_half_finalassignments[delegate]
            otherCountrySuggestionsDictionary = suggest_countries_based_on_ranking(school_status, tier1, tier2, other_half_finalassignments, preferences, availableCountries)
            countrySuggestionsDictionary = firstcountrySuggestionsDictionary | otherCountrySuggestionsDictionary

        elif numdels < 30 and sanitized_school_name not in blacklist:
            countrySuggestionsDictionary = suggest_countries_based_on_ranking(school_status, tier1, tier2, finalassignments, preferences, availableCountries)

        elif sanitized_school_name in blacklist:
            countrySuggestionsDictionary = suggest_countries_for_blacklisted_school(finalassignments, tier1, tier2, availableCountries, preferences)
        else: return None

    elif blacklist is None:
        if numdels >= 30:
            half1 = numdels//2; half2 = (numdels//2)+(numdels%2)
            firstcountrySuggestionsDictionary, already_suggested_delegates = suggest_p5_countries(top5, half1, preferences, finalassignments, availableCountries)
            other_half_finalassignments = finalassignments
            for delegate in already_suggested_delegates:
                del other_half_finalassignments[delegate]
            otherCountrySuggestionsDictionary = suggest_countries_based_on_ranking(school_status, tier1, tier2, other_half_finalassignments, preferences, availableCountries)
            countrySuggestionsDictionary = firstcountrySuggestionsDictionary | otherCountrySuggestionsDictionary

        elif numdels < 30:
            countrySuggestionsDictionary = suggest_countries_based_on_ranking(school_status, tier1, tier2, finalassignments, preferences, availableCountries)
        else: return None
    else: return None
            
    return countrySuggestionsDictionary

def suggest_countries_based_on_ranking(school_status, tier1, tier2, finalassignments, preferences, availableCountries) -> dict[str, list[str]]:
    """
    Keep track of countries already suggested. If suggested more than 4 times in the list, do not suggest that country again.

    Go through each delegate and allocate countries randomly based on status, then committee availability, then country preferences

    Country preferences of the school is selected manually. Interface simply prints the country preferences available in this committee.

    There is a careful dictionary linking logic inside of here that ensures the variables in the dictionary and the loop get updated when needed for ignoring countries.
    """
    SuggestionsDictionary = {}
    already_suggested_countries = []
    ignored_countries = []
    committee_availability = {} # a dictionary that saves availability data from past iterations

    if school_status == "great":
        assignments = (0, 3, 3) # take 2 from tier 1, 3 from tier 2, and 4 from tier 3
    elif school_status == "good":
        assignments = (1, 2, 3)
    elif school_status == "below average":
        assignments = (2, 3, 1)
    elif school_status == "unexperienced":
        assignments = (3, 2, 0)
    else:
        Display.display("")
        sys.exit(1)

    SuggestionsDictionary = generate_suggestions_for_delegates(finalassignments, tier1, tier2, availableCountries, preferences, already_suggested_countries, ignored_countries, committee_availability, assignments, SuggestionsDictionary)
    return SuggestionsDictionary

def suggest_p5_countries(top5, half1, preferences, finalassignments, availableCountries) -> tuple[dict[str, list[str]], set]:
    # do not take into account preferences. Since there are only 5 top countries anyways, just give them random selections.
    already_suggested_delegates = set()
    countrySuggestionsDictionary = {}
    for index, (delegate_key, [committee, comm_type, country]) in enumerate(finalassignments.items()):

        if index == half1: # once we get this number of delegates, we stop.
            break
        # Only process General Assembly (GA) committees
        if comm_type.upper() != "GA":
            continue

        # 1. Filter available countries specifically for this delegate's committee, based on if in top5 and if in preferences in committee.
        top5 = {country.strip().lower() for country in top5}
        top5_available_for_comm = [country.strip() for comm, country in availableCountries if comm.strip().lower() == committee.lower() and country.strip().lower() in top5]
        preferences_in_committee = [country for country in top5_available_for_comm if country in preferences]

        countrySuggestionsDictionary[delegate_key] = (top5_available_for_comm, preferences_in_committee)
        already_suggested_delegates.add(delegate_key)

    return countrySuggestionsDictionary, already_suggested_delegates

def suggest_countries_for_blacklisted_school(finalassignments, tier1, tier2, availableCountries, preferences) -> dict[str, list[str]]:
    SuggestionsDictionary = {}
    already_suggested_countries = []
    ignored_countries = []
    committee_availability = {}

    assignments = (0, 3, 3)
    SuggestionsDictionary = generate_suggestions_for_delegates(finalassignments, tier1, tier2, availableCountries, preferences, already_suggested_countries, ignored_countries, committee_availability, assignments, SuggestionsDictionary)

    return SuggestionsDictionary

def generate_suggestions_for_delegates(finalassignments, tier1, tier2, availableCountries, preferences, already_suggested_countries: list[str], ignored_countries: list[str], committee_availability, assignments, SuggestionsDictionary):
    for delegate_key, details in finalassignments.items():
        committee = details[0]
        comm_type = details[1]
        preferences_in_committee = set()
        
        # Only process General Assembly (GA) committees
        if comm_type.upper() != "GA":
            continue

        # 1. Filter available countries specifically for this delegate's committee
        available_for_comm = [country.strip().upper() for comm, country in availableCountries if comm.strip().lower() == committee.lower()]

        if committee in committee_availability.keys():
            tiers = committee_availability[committee]
            if already_suggested_countries is not None and already_suggested_countries != []:
                assigned_number_of_times = Counter(already_suggested_countries)
                for repeated_country, repeats in assigned_number_of_times.items():
                    if repeats == 4 and repeated_country not in ignored_countries:
                        if repeated_country in tiers["tier1"]:
                            # notice, we directly modify that variable stored inside the dictionary.
                            tiers["tier1"][:] = [name for name in tiers["tier1"] if name != repeated_country]
                        if repeated_country in tiers["tier2"]:
                            tiers["tier2"][:] = [name for name in tiers["tier2"] if name != repeated_country]
                        if repeated_country in tiers["tier3"]:
                            tiers["tier3"][:] = [name for name in tiers["tier3"] if name != repeated_country]
                        ignored_countries.append(repeated_country)
            unique_available_tier1 = committee_availability[committee]["tier1"]
            unique_available_tier2 = committee_availability[committee]["tier2"]
            unique_available_tier3 = committee_availability[committee]["tier3"]
        else:
            unique_available_tier1 = list(set([country for country in available_for_comm if country in tier1]))
            unique_available_tier2 = list(set([country for country in available_for_comm if country in tier2]))
            unique_available_tier3 = list(set([country for country in available_for_comm if country not in tier1 and country not in tier2]))
            committee_availability[committee] = {"tier1": unique_available_tier1, "tier2": unique_available_tier2, "tier3": unique_available_tier3}
            tiers = committee_availability[committee]
            assigned_number_of_times = Counter(already_suggested_countries)
            for repeated_country, repeats in assigned_number_of_times.items():
                if repeats == 4 and repeated_country not in ignored_countries:
                    if repeated_country in tiers["tier1"]:
                        # notice, we directly modify that variable stored inside the dictionary.
                        tiers["tier1"][:] = [name for name in tiers["tier1"] if name != repeated_country]
                    if repeated_country in tiers["tier2"]:
                        tiers["tier2"][:] = [name for name in tiers["tier2"] if name != repeated_country]
                    if repeated_country in tiers["tier3"]:
                        tiers["tier3"][:] = [name for name in tiers["tier3"] if name != repeated_country]
                    ignored_countries.append(repeated_country)

        delegate_country_suggestions = []
        # the code segment here picks from the tier lists based on how many to choose from.
        if len(unique_available_tier1) >= assignments[0]:
            suggestions = random.sample(unique_available_tier1, k=assignments[0])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        if len(unique_available_tier2) >= assignments[1]:
            suggestions = random.sample(unique_available_tier2, k=assignments[1])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        if len(unique_available_tier3) >= assignments[2]:
            suggestions = random.sample(unique_available_tier3, k=assignments[2])
            for suggestion in suggestions:
                delegate_country_suggestions.append(suggestion)
                already_suggested_countries.append(suggestion)
        # process preferences that are in the delegate's committee and store in a list. Have the dictionary value
        # for SuggestionsDictionary be a tuple, where first value is the list of suggestions for that delegate, 
        # and second value is the list of preferences available in that committee.
        for preference in preferences:
            if preference in available_for_comm:
                preferences_in_committee.add(preference)
        SuggestionsDictionary[delegate_key] = (delegate_country_suggestions, preferences_in_committee)

    return SuggestionsDictionary
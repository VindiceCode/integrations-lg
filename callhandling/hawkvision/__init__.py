import logging
import os
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest, SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException
from hubspot.auth.oauth import ApiException 
import hubspot  
import azure.functions as func
from ratelimiter import RateLimiter
import json



# Define keyword mappings to internal values
CONTENT_HARD_MATCH_STAGES = {
    #OptOut Comes First to ensure DNC Terms Prioritized
    "Hard DNC Language": {
        "InternalValue": 177397,
        "Keywords": [
            "opt me out", "opt us out", "stop", "opt out", "do not contact",
            "don't contact", "stop!", "shtop", "dnc", "delete", "delete", "dnc","please remove","don't text", "don't message", "don't call", "don't text me", "don't message me", "don't call me", "don't contact me", "don't reach out"
        ]
    },
    "Wrong Number": {
        "InternalValue": 170391,
        "Keywords": [
            "wrong number", "this is not", "this isn't"
        ]
    },
    "Do not want a response": {
        "InternalValue": 170389,
        "Keywords": [
            "hell", "fuck", "suck", "remove", "leave alone",
            "didn't give permission", "stop harassing", "do not text me",
            "sketchy", "take me off your", "take me off list", "take off list",
            "ass", "asshole", "f off", "asshole", "remove my", "bother me",
            "reach out", "do not message", "do not text", "lawyer", "sue",
            "legal action", "fraud", "illegal"
        ]
    },
    "Land Loan": {
        "InternalValue": 170388,
        "Keywords": [
            "land loan", "land"
        ]
    },
     "Ask For LE / Already in Process": {
        "InternalValue": 104247,
        "Keywords": [
            "locked", "contract", "closing date", "closing"
        ]
    },
    "HELOC / No Cash-Out Intention": {
        "InternalValue": 39143,
        "Keywords": [
            "HELOC", "HELOAN", "Equity Line"
        ]
    },
    "Spanish": {
        "InternalValue": 170449,
        "Keywords": [
            "habla", "Espanol", "ITIN", "Spanish"
        ]
    },
    "Not Interested": {
        "InternalValue": 39140,
        "Keywords": [
            "no thank you", "no", "you are spam", "i'm not interested, thank you",
            "all good", "i'm okay", "i'm all set thank you", "u+1f44e",
            "i'm not looking for a mortgage", "all set",
            "no thx", "why are you texting me? i'm set up already. thks",
            "i'm looking into that right now", "i do not need your services",
            "hi, i don't. thanks", "all set, ty", "i do not need any services. thank you",
            "don't need ya", "neither one i'm good thank you", "i don't need a new mortgage",
            "not interested", "i'm not looking to refi or purchase", "i am no longer taking estimates",
            "not looking for new home options", "how about no", "we are all set",
            "have everything covered", "we are good", "do not need your services",
            "i am good for now", "isn't something i'd like to do", "not interested"
        ]
    }
}

CONTENT_STRICT_MATCH_STAGES = {
}

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
         # Parse the JSON payload from the request body
        payload = req.get_json()
        # Print the JSON payload
        print(f"Payload: {payload}")
        prospect = payload.get('prospect', {})
        first_name = prospect.get('first_name', '')
        last_name = prospect.get('last_name', '')
        full_name = prospect.get('full_name', '')
        phone_number = prospect.get('phone', '')
        address = prospect.get('address', '')
        city = prospect.get('city', '')
        state = prospect.get('state', '')
        zip_code = prospect.get('zip', '')
        assigned_to = prospect.get('assigned_to')
        assigned_to = str(assigned_to)
        tags = prospect.get('tags', '')
        dnc = prospect.get('dnc', '')
        created_at = prospect.get('created_at', '')
        updated_at = prospect.get('updated_at', '')
        prospect_id = prospect.get('id', '')
        # Initialize a dictionary to store the associations between IDs and names
        id_to_name = {}

        # Assume you have a list of tuples, where each tuple contains a unique ID and a name
        associations = [("6387", "Joe Prepolec"), ("6416", "Chaz Wenzel"), ("21999", "Chaz Wenzel"), ("22000", "Chaz Wenzel"), ("22001", "Chaz Wenzel"), ("22002", "Chaz Wenzel"), ("22003", "Chaz Wenzel"), ("22009", "Chaz Wenzel"), ("22004", "Chaz Wenzel"), ("14138", "Corie Walker"), ("21799", "Corie Walker"), ("22011", "Corie Walker"), ("22012", "Corie Walker"), ("22013", "Corie Walker"), ("22014", "Corie Walker"), ("22015", "Corie Walker"), ("22016", "Corie Walker"), ("22017", "Corie Walker"), ("11126", "Dani Hardy"), ("21798", "Dani Hardy"), ("22025", "Dani Hardy"), ("22026", "Dani Hardy"), ("22027", "Dani Hardy"), ("22028", "Dani Hardy"), ("22029", "Dani Hardy"), ("22030", "Dani Hardy"), ("22031", "Dani Hardy"), ("16469", "Eric Rayner"), ("21800", "Eric Rayner"), ("22034", "Eric Rayner"), ("22035", "Eric Rayner"), ("22037", "Eric Rayner"), ("22038", "Eric Rayner"), ("22039", "Eric Rayner"), ("22040", "Eric Rayner"), ("22041", "Eric Rayner"), ("18220", "Evan Walker"), ("21801", "Evan Walker"), ("22053", "Evan Walker"), ("22054", "Evan Walker"), ("22055", "Evan Walker"), ("22056", "Evan Walker"), ("22057", "Evan Walker"), ("22058", "Evan Walker"), ("22059", "Evan Walker"), ("18221", "Ian Evans"), ("21802", "Ian Evans"), ("22045", "Ian Evans"), ("22046", "Ian Evans"), ("22047", "Ian Evans"), ("22048", "Ian Evans"), ("22049", "Ian Evans"), ("22050", "Ian Evans"), ("22051", "Ian Evans"), ("7395", "Ian Melchor"), ("21795", "Ian Melchor"), ("22063", "Ian Melchor"), ("22064", "Ian Melchor"), ("22065", "Ian Melchor"), ("22066", "Ian Melchor"), ("22067", "Ian Melchor"), ("22068", "Ian Melchor"), ("22069", "Ian Melchor"), ("11125", "Kemuel Veloz"), ("21797", "Kemuel Veloz"), ("22074", "Kemuel Veloz"), ("22075", "Kemuel Veloz"), ("22076", "Kemuel Veloz"), ("22077", "Kemuel Veloz"), ("22078", "Kemuel Veloz"), ("22079", "Kemuel Veloz"), ("6413", "Melanie Trinh"), ("9934", "Sean Muscaro")]
        # Populate the dictionary with the associations
        for id, name in associations:
            id_to_name[id] = name

        #Access the Additional Top-End Object and Message Objects
        additional = payload.get('additional')
        message = additional.get('message')
        content = message.get('content')
        event_date = message.get('event_date')

        # Check if tags is 'acknowledged'
        if tags == 'acknowledged':
            return func.HttpResponse("Tags is 'acknowledged'. Not creating a HubSpot contact.", status_code=200)
        
         # Check if tags is 'Acknowledged'
        if tags == 'Acknowledged':
            return func.HttpResponse("Tags is 'acknowledged'. Not creating a HubSpot contact.", status_code=200)
        #Transform Message Content into ascii string
        import re
        ascii_content = re.sub(r'[^\x00-\x7F]+', '_', content)
        
        # Check if dnc is Trues
        if dnc is True:
            return func.HttpResponse("DNC is True. Not creating a HubSpot contact.", status_code=200)
        
        # Default internal value
        internal_value = "39142"  # Default internal value if no keyword matches
        for stage_name, stage_info in CONTENT_HARD_MATCH_STAGES.items():
            for keyword in stage_info["Keywords"]:
                import re
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, ascii_content.lower()):
                    internal_value = stage_info["InternalValue"]
                    logging.info(f"Keyword '{keyword}' Hard matched with stage '{stage_name}' with InternalValue: {internal_value}")
                    break
            else:
                continue  # only executed if the inner loop did NOT break
            break  # first break exits the inner loop, this break exits the outer loop

        logging.info(f"Proceeding with contact creation/update with InternalValue: {internal_value}")
        

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, full_name, phone_number, address, city, state, zip_code, assigned_to, tags, dnc, created_at, updated_at, prospect_id, message]
        

         # Initialize the HubSpot API Client
        access_token = os.getenv('hubspot_privateapp_access_token')
        client = hubspot.Client.create(access_token=access_token)

        # Check if a contact with the same phone number already exists
        filter = Filter(
            property_name="phone",
            operator="EQ",
            value=phone_number
        )
        
        filter_group = FilterGroup(filters=[filter])
        search_request = PublicObjectSearchRequest(filter_groups=[filter_group])
        try:
            # Initialize a Rate Limiter Instance for Hubspot Search 4_1 API Limits
            rate_limiter_4_1 = RateLimiter(max_calls=4, period=1)
            with rate_limiter_4_1:
                existing_contacts = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                
                # Check if existing contacts were found
                if existing_contacts and existing_contacts.total > 0:
                    return func.HttpResponse("Contact already exists.", status_code=200)
        except ApiException as e:
            if e.status != 404:  # If the status code is not 404, re-raise the exception
                raise

        # Create a RateLimiter instance
        rate_limiter_150_10 = RateLimiter(max_calls=150, period=10)
        existing_contacts = None

    
        if existing_contacts is None or len(existing_contacts.results) == 0:
        # Create a contact

            with rate_limiter_150_10:
                # Assume assigned_to is a unique ID
                assigned_to_name = id_to_name[assigned_to]
                simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
                    properties={
                        "firstname": first_name,
                        "lastname": last_name,
                        "phone": phone_number,
                        "address": address,
                        "city": city,
                        "state": state,
                        "zip": zip_code,
                        "bonzo_owner": assigned_to_name,
                        "bonzo_create_date": created_at,
                        "time_of_bonzo_response": event_date,
                        "bonzo_prospect_id": prospect_id,
                        "industry": prospect_id,
                        "bonzo_lead_initial_response": ascii_content,
                        "website": f"https://platform.getbonzo.com/prospect/{prospect_id}",
                        "annualrevenue": assigned_to,
                        "bonzo_pipeline_stage": internal_value,
                    }
                )
                api_response = client.crm.contacts.basic_api.create(
                    simple_public_object_input_for_create=simple_public_object_input_for_create
                )
                
                print(api_response)

        return func.HttpResponse("Success! Hawkvision Contact Created in Hubspot - One Step Closer to World Domination!", status_code=200)


    except ValueError as ve:
        logging.error(f"ValueError: {str(ve)}")
        return func.HttpResponse("Invalid input", status_code=400)

    except requests.exceptions.RequestException as re:
        logging.error(f"RequestException: {str(re)}")
        return func.HttpResponse("An error occurred while making a request", status_code=500)

    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return func.HttpResponse("An error occurred", status_code=500)
    
    except ApiException as ae:
        logging.error(f"ApiException: {str(ae)}")
        return func.HttpResponse("An error occurred while creating the contact in HubSpot", status_code=500)(

        )
import logging
import os
import re
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest, SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException
from hubspot.auth.oauth import ApiException 
import hubspot  
import azure.functions as func
from ratelimiter import RateLimiter
import json
import time


# Define keyword mappings to internal values
CONTENT_HARD_MATCH_STAGES = [
    #OptOut Comes First to ensure DNC Terms Prioritized
    {
        "type" : "Hard DNC Language",
        "InternalValue": 177397,
        "Keywords": [
            "opt me out", "opt us out", "stop", "opt out", "do not contact",
            "don't contact", "stop!", "shtop", "dnc", "delete", "delete", "dnc","please remove","don't text", "don't message", "don't call", "don't text me", "don't message me", "don't call me", "don't contact me", "don't reach out"
            ]
        }
    ,
    {
        "type":"Wrong Number",
        "InternalValue": 170391,
        "Keywords": [
            "wrong number", "this is not", "this isn't"
            ]
        }
    ,
    {
        "type":"Do not want a response",
        "InternalValue": 170389,
        "Keywords": [
            "hell", "fuck", "suck", "remove", "leave alone",
            "didn't give permission", "stop harassing", "do not text me",
            "sketchy", "take me off your", "take me off list", "take off list",
            "ass", "asshole", "f off", "asshole", "remove my", "bother me",
            "reach out", "do not message", "do not text", "lawyer", "sue",
            "legal action", "fraud", "illegal"
            ]
        }
    ,
    {
        "type":"Land Loan",
        "InternalValue": 170388,
        "Keywords": [
            "land loan", "land"
            ]
        }
    ,
    {
        "type": "Ask For LE / Already in Process",
        "InternalValue": 104247,
        "Keywords": [
            "locked", "contract", "closing date", "closing"
            ]
        }
    ,
    {
        "type":"HELOC / No Cash-Out Intention",
        "InternalValue": 39143,
        "Keywords": [
            "HELOC", "HELOAN", "Equity Line"
            ]
        }
    ,
    {
        "type":"Spanish",
        "InternalValue": 170449,
        "Keywords": [
            "habla", "Espanol", "ITIN", "Spanish"
            ]
        }
    ,
    {
        "type":"Not Interested",
        "InternalValue": 39140,
        "Keywords": [
            "no thank you", "no", "you are spam", "i'm not interested, thank you",
            "all good", "i'm okay", "i'm all set thank you", "u+1f44e",
            "i'm not looking for a mortgage", "all set",
            "no thx", "why are you texting me? i'm set up already. thks", "i do not need your services",
            "hi, i don't. thanks", "all set, ty", "i do not need any services. thank you",
            "don't need ya", "neither one i'm good thank you", "i don't need a new mortgage",
            "not interested", "i'm not looking to refi or purchase", "i am no longer taking estimates",
            "not looking for new home options", "how about no", "we are all set",
            "have everything covered", "we are good", "do not need your services",
            "i am good for now", "isn't something i'd like to do", "not interested"
            ]
        }   
]


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        logging.info(f"payload  : {payload}")
        prospect = payload.get('prospect', {})
        first_name = prospect.get('first_name', '')
        last_name = prospect.get('last_name', '')
        full_name = prospect.get('full_name', '')
        phone_number = prospect.get('phone', '')
        address = prospect.get('address', '')
        city = prospect.get('city', '')
        state = prospect.get('state', '')
        zip_code = prospect.get('zip', '')
        assigned_to = str(prospect.get('assigned_to'))
        tags = prospect.get('tags', [])
        dnc = prospect.get('dnc', '')
        created_at = prospect.get('created_at', '')
        updated_at = prospect.get('updated_at', '')
        prospect_id = prospect.get('id', '')
        id_to_name = {
            '6413': 'Melanie Trinh',
            '6416': 'Chaz Wenzel',
            '7395': 'Ian Melchor',
            '9934': 'Sean Muscaro',
            '11125': 'Kemuel Veloz',
            '11126': 'Dani Hardy',
            '14138': 'Corinne Walker',
            '16469': 'Eric Rayner',
            '18220': 'Evan Walker',
            '18221': 'Ian Evans'
            }
        additional = payload.get('additional',None)
        if additional:
            message = additional.get('message',None)
            if message:
                content = message.get('content')
                event_date = message.get('event_date')
        if 'acknowledged' in tags or "Acknowledge" in tags:
            logging.info(f"Tags is 'acknowledged'. Not creating a HubSpot contact.")
            return func.HttpResponse("Tags is 'acknowledged'. Not creating a HubSpot contact.", status_code=200)
        
        if dnc is True:
            logging.info(f"DNC is True. Not creating a HubSpot contact.")
            return func.HttpResponse("DNC is True. Not creating a HubSpot contact.", status_code=400)
        #Transform Message Content into ascii string
        # Default internal value
        ascii_content_lower = re.sub(r'[^\x00-\x7F]+', ' ', content).lower()
        internal_value = "39142"
        for key in CONTENT_HARD_MATCH_STAGES:
            keywords = [rf'{re.escape(keyword.lower())}' for keyword in key['Keywords']]
            pattern = '|'.join(keywords)
            if re.search(pattern, ascii_content_lower):
                internal_value = key['InternalValue']
                type = key["type"]
                logging.info(f"Keyword '{pattern}' Hard matched with stage '{type}' with InternalValue: {internal_value}")
                break

        logging.info(f"Proceeding with contact creation/update with InternalValue: {internal_value}")
        
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
            time.sleep(1)
            existing_contacts = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                # Check if existing contacts were found
            if existing_contacts and existing_contacts.total > 0:
                return func.HttpResponse("Contact already exists.", status_code=200)
            else :
                if assigned_to in id_to_name:
                    assigned_to_name = id_to_name[assigned_to]
                    logging.info(f"Assigned to name: {assigned_to_name}")
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
                        "bonzo_lead_initial_response": ascii_content_lower,
                        "website": f"https://platform.getbonzo.com/prospect/{prospect_id}",
                        "annualrevenue": assigned_to,
                        "bonzo_pipeline_stage": internal_value,
                    }
                    )
                    time.sleep(1)
                    api_response = client.crm.contacts.basic_api.create(
                        simple_public_object_input_for_create=simple_public_object_input_for_create
                    )
                    logging.info(f"Contact creted Api response: {api_response}")
                    return func.HttpResponse("Success! Incoming sms Contact Created in Hubspot - One Step Closer to World Domination!", status_code=200)
                logging.warning(f"Assigned to ID {assigned_to} not found in the dictionary")
                return func.HttpResponse(f"Assigned to ID {assigned_to} not found in the dictionary", status_code=400)
        except ApiException as e:
            if e.status != 404:  # If the status code is not 404, re-raise the exception
                raise            
        except ValueError as ve:
            logging.error(f"ValueError: {str(ve)}")
            return func.HttpResponse("Invalid input", status_code=400)

        except requests.exceptions.RequestException as err:
            logging.error(f"RequestException: {str(err)}")
            return func.HttpResponse("An error occurred while making a request", status_code=500)

        except Exception as e:
            logging.error(f"Exception: {str(e)}")
            return func.HttpResponse("An error occurred", status_code=500)
    
    except ApiException as ae:
        logging.error(f"ApiException: {str(ae)}")
        return func.HttpResponse("An error occurred while creating the contact in HubSpot", status_code=500)(

        )
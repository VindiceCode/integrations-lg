import logging
import os
import csv
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest, SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException
from hubspot.auth.oauth import ApiException 
import hubspot  
import azure.functions as func
from ratelimiter import RateLimiter

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
         # Parse the JSON payload from the request body
        payload = req.get_json()
        # Print the JSON payload
        print(f"Payload: {payload}")
        prospect = payload.get('prospect')
        first_name = prospect.get('first_name')
        last_name = prospect.get('last_name')
        full_name = prospect.get('full_name')
        phone_number = prospect.get('phone')
        address = prospect.get('address')
        city = prospect.get('city')
        state = prospect.get('state')
        zip_code = prospect.get('zip')
        assigned_to = prospect.get('assigned_to')
        assigned_to = str(assigned_to)
        tags = prospect.get('tags')
        dnc = prospect.get('dnc')
        created_at = prospect.get('created_at')
        updated_at = prospect.get('updated_at')
        prospect_id = prospect.get('id')

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

        

        # Check if "Acknowledged" is in tags
        if tags is not None and "Acknowledged" in tags:
            return func.HttpResponse("Tag 'Acknowledged' found. Not creating a HubSpot contact.", status_code=200)

        # Check if dnc is True
        if dnc is True:
            return func.HttpResponse("DNC is True. Not creating a HubSpot contact.", status_code=200)

        # Check if the message includes "stop" or "not interested"
        if message is not None and ('stop' in message or 'STOP' in message or 'not interested' in message):
            return func.HttpResponse("Message includes 'stop' or 'not interested'. Not creating a HubSpot contact.", status_code=200) 

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, full_name, phone_number, address, city, state, zip_code, assigned_to, tags, dnc, created_at, updated_at, prospect_id, message]
        
        # Create a RateLimiter instance
        rate_limiter = RateLimiter(max_calls=148, period=10)
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
            existing_contacts = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        except ApiException as e:
            if e.status != 404:  # If the status code is not 404, re-raise the exception
                raise

            existing_contacts = None

        if existing_contacts is None or len(existing_contacts.results) == 0:
        # Create a contact
            with rate_limiter:
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
                        "bonzo_lead_initial_response": content,
                        "website": f"https://platform.getbonzo.com/prospect/{prospect_id}"
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
        return func.HttpResponse("An error occurred while creating the contact in HubSpot", status_code=500)
import logging
import os
import csv
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException
from hubspot.auth.oauth import ApiException  # Add this line
import hubspot  # Add this line
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse the JSON payload from the request body
        payload = req.get_json()
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
        tags = prospect.get('tags')
        dnc = prospect.get('dnc')
        created_at = prospect.get('created_at')
        updated_at = prospect.get('updated_at')
        prospect_id = prospect.get('prospect_id')

        #Access the Additional Top-End Object and Message Objects
        additional = payload.get('additional')
        message = additional.get('message').get('content')
        content = message.get('content')
        event_date = message.get('event_date')

        # Check if "Acknowledged" is in tags
        if tags is not None and "Acknowledged" in tags:
            return func.HttpResponse("Tag 'Acknowledged' found. Not creating a HubSpot contact.", status_code=200)

        # Check if dnc is True
        if dnc is True:
            return func.HttpResponse("DNC is True. Not creating a HubSpot contact.", status_code=200)

        # Check if the message includes "stop" or "not interested"
        if message is not None and ('stop' in message.lower() or 'not interested' in message.lower()):
            return func.HttpResponse("Message includes 'stop' or 'not interested'. Not creating a HubSpot contact.", status_code=200)
       
        
        # Initialize the HubSpot API Client
        access_token = os.getenv('hubspot_privateapp_access_token')  # Modify this line
        print(f"Access token: {access_token}")  # Add this line
        client = hubspot.Client.create(access_token=access_token)  # Modify this line

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, full_name, phone_number, address, city, state, zip_code, assigned_to, tags, dnc, created_at, updated_at, prospect_id, message]

        # Create a contact
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties={
                "firstname": first_name,
                "lastname": last_name,
                "phone": phone_number,
                "address": address,
                "city": city,
                "state": state,
                "zip": zip_code,
                "bonzo_owner": assigned_to,
                "bonzo_create_date": created_at,
                "time_of_bonzo_response": event_date,
                "bonzo_propsect_id": prospect_id,
                "bonzo_lead_initial_response": message  
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
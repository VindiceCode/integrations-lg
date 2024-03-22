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
        # Parse the query parameters from the request URL
        query_params = req.params
        first_name = query_params.get('firstName')
        last_name = query_params.get('lastName')
        phone_number = query_params.get('phoneNumber')
        email = query_params.get('email')

        # Check if all required parameters are provided
        if not first_name or not last_name or not phone_number:
            return func.HttpResponse(
                "Please provide all required parameters: firstName, lastName, phoneNumber",
                status_code=400
            )
        
        # Check that the properties are in the correct format
        assert isinstance(first_name, str), "First name must be a string"
        assert isinstance(last_name, str), "Last name must be a string"
        
        # Initialize the HubSpot API Client
        access_token = os.getenv('hubspot_privateapp_access_token')  # Modify this line
        print(f"Access token: {access_token}")  # Add this line
        client = hubspot.Client.create(access_token=access_token)  # Modify this line

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, phone_number]

        # Create a contact
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties={
                "firstname": first_name,
                "lastname": last_name,
                "phone": phone_number,
                "email": email
            }
        )
        api_response = client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=simple_public_object_input_for_create
        )

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
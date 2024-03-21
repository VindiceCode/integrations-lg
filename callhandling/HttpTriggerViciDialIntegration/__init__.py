import logging
import os
import csv
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from hubspot.crm.contacts.exceptions import ApiException
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

        # Initialize the HubSpot API Client
        api_key = "pat-na1-d9d61458-1ee0-4912-851f-da86be8286b6"
        api_client = HubSpot(api_key=api_key)

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, phone_number]

        # Log the captured properties
        logging.info(f"Captured properties: {captured_properties}")

        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties={
                "firstname": first_name,
                "lastname": last_name,
                "phone": phone_number,
                "email": email
            }
        )
        api_response = api_client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=simple_public_object_input_for_create
        )

        # Get the ID of the newly created contact
        contact_id = api_response.id

        # Construct the URL to the contact in the HubSpot web interface
        hub_id = 44341454
        contact_url = f"https://app.hubspot.com/contacts/{hub_id}/contact/{contact_id}"

        # Return the success response with the link to the created contact
        response = f"Contact Created in Hubspot with ID: {contact_id}\n\n"
        response += f"Captured parameters:\n"
        response += f"First Name: {first_name}\n"
        response += f"Last Name: {last_name}\n"
        response += f"Phone Number: {phone_number}\n"
        response += f"Email: {email}\n"
        response += f"Contact URL: {contact_url}\n"
        return func.HttpResponse(response)

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
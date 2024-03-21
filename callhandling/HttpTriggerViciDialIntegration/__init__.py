import logging
import csv
import requests

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

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, phone_number]

        # Log the captured properties
        logging.info(f"Captured properties: {captured_properties}")

        # Perform the necessary operations to create the contact in Hubspot
        # ...

        # Return the success response with the link to the created contact
        response = f"Contact Created in Hubspot - LINK GOES HERE\n\n"
        response += f"Captured parameters:\n"
        response += f"First Name: {first_name}\n"
        response += f"Last Name: {last_name}\n"
        response += f"Phone Number: {phone_number}\n"
        response += f"Email: {email}\n"
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

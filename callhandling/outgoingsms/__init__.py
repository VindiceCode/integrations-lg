import logging
import os
import json
import azure.functions as func
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput, Filter, FilterGroup, PublicObjectSearchRequest
from hubspot.crm.contacts.exceptions import ApiException
import ratelimiter
from datetime import datetime
import pytz
import time


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        # logging.info(f"Payload: {payload}")

        event_type = payload.get('event')
        if event_type != 'messages.outgoing.created':
            logging.info(f"This is not the outgoing created message")
            return func.HttpResponse("This function only handles outgoing messages.", status_code=400)

        # Access the Additional Top-End Object and Message Objects
        additional = payload.get('additional', {})
        message = additional.get('message', {})
        content = message.get('content')
        prospect = payload.get('prospect', {})
        phone_number = prospect.get('phone')
        
        smscreatedate = additional.get('message', {}).get('created_at', {})

        if not phone_number:
            logging.info(f"No phone number provided in the payload.")
            return func.HttpResponse("No phone number provided in the payload.", status_code=400)

        client = HubSpot(access_token=os.getenv('hubspot_privateapp_access_token'))

        # Search for existing contact
        filter = Filter(property_name="phone", operator="EQ", value=phone_number)
        filter_group = FilterGroup(filters=[filter])
        search_request = PublicObjectSearchRequest(filter_groups=[filter_group])

        # Rate limit the search API
        search_response = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        time.sleep(1)

        if search_response.total > 0:
            existing_contacts = search_response.results
            contact_id = existing_contacts[0].id  
            # Prepare properties to update
            properties_to_update = {
                "sales_sms_out_latest": content,
                "latest_sms_create_date": smscreatedate,
            }

            # Update the contact in HubSpot
            update_response = client.crm.contacts.basic_api.update(
                contact_id,
                SimplePublicObjectInput(properties=properties_to_update)
            )
            time.sleep(1)
            return func.HttpResponse(f"Successfully updated HubSpot contact {contact_id}.", status_code=200)
        else:
            logging.info(f"No corresponding contact found in HubSpot; outgoing message not logged.")
            return func.HttpResponse("No corresponding contact found in HubSpot; outgoing message not logged.", status_code=400)

    except ApiException as e:
        logging.error(f"ApiException: {str(e)}")
        return func.HttpResponse(f"An error occurred while interacting with HubSpot API: {str(e)}", status_code=500)
    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return func.HttpResponse("An error occurred while processing the request.", status_code=500)
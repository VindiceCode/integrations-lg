Ideal Integrations Project File Structure Psuedocode (Click "Edit" to see it formatted correctly"

Pseudocode structure:

├── integrations-lg/
│ ├── smshandling/
│ │ ├── incomingsms/
│ │ │ ├── __init__.py
│ │ │ ├── sms_in_initialreply/
│ │ │ │ ├── __init__.py
│ │ │ │ └── sms_in_initialreply_logic.py 
│ │ │ ├── sms_in_hscontact/
│ │ │ │ ├── __init__.py
│ │ │ │ └── sms_in_hscontact_logic.py 
│ │ │ ├── sms_in_pipeline_stage/
│ │ │ │ ├── __init__.py
│ │ │ │ └── sms_in_pipeline_stage_logic.py 
│ │ │ ├── function.json
│ │ ├── outgoingsms/
│ │ │ ├── __init__.py
│ │ │ ├── sms_out_main/
│ │ │ │ ├── __init__.py
│ │ │ │ └── sms_out_main_logic.py 
│ │ │ ├── function.json
│ │ ├── utils.py
│ │ ├── constants.py
│ │ ├── rate_limiter.py
│ │ ├── hubspot_client.py
│ │ ├── host.json
│ │ └── requirements.txt
│ └── ...

Each function should have its own directory with an `__init__.py` file and a `logic.py` file containing the function's execution logic. 

The `function.json` file should be placed in the parent directory of the functions it corresponds to (e.g., in the `incomingsms` directory for functions that handle incoming SMS messages).


constants.py
----------
CONTENT_HARD_MATCH_STAGES = {
    ...
}

CONTENT_STRICT_MATCH_STAGES = {
    ...
}

ASSOCIATIONS = [
    ...
]

rate_limiter.py
---------------
import RateLimiter

def create_rate_limiter_4_1():
    return RateLimiter(max_calls=4, period=1)

def create_rate_limiter_150_10():
    return RateLimiter(max_calls=150, period=10)

hubspot_client.py
-----------------
import os
import hubspot
from hubspot.crm.contacts import Filter, FilterGroup, PublicObjectSearchRequest, SimplePublicObjectInputForCreate
from hubspot.auth.oauth import ApiException

def create_client():
    access_token = os.getenv('hubspot_privateapp_access_token')
    return hubspot.Client.create(access_token=access_token)

def search_contacts(client, phone_number):
    filter = Filter(property_name="phone", operator="EQ", value=phone_number)
    filter_group = FilterGroup(filters=[filter])
    search_request = PublicObjectSearchRequest(filter_groups=[filter_group])
    try:
        existing_contacts = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        return existing_contacts
    except ApiException as e:
        if e.status != 404:
            raise

def create_contact(client, contact_data):
    simple_public_object_input_for_create = SimplePublicObjectInputForCreate(properties=contact_data)
    api_response = client.crm.contacts.basic_api.create(simple_public_object_input_for_create=simple_public_object_input_for_create)
    return api_response

utils.py
--------
import re

def get_id_to_name_mapping(associations):
    id_to_name = {}
    for id, name in associations:
        id_to_name[id] = name
    return id_to_name

def transform_message_content(content):
    ascii_content = re.sub(r'[^\x00-\x7F]+', '_', content)
    return ascii_content

def check_dnc(dnc):
    return dnc is True

def check_tags(tags):
    return tags == 'acknowledged' or tags == 'Acknowledged'

def find_keyword_match(content, content_hard_match_stages):
    internal_value = "39142"
    for stage_name, stage_info in content_hard_match_stages.items():
        for keyword in stage_info["Keywords"]:
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, content.lower()):
                internal_value = stage_info["InternalValue"]
                break
        else:
            continue
        break
    return internal_value

sms_in_main.py
-------
import logging
import os
import azure.functions as func
from .utils import get_id_to_name_mapping, transform_message_content, check_dnc, check_tags, find_keyword_match
from .hubspot_client import create_client, search_contacts, create_contact
from .rate_limiter import create_rate_limiter_4_1, create_rate_limiter_150_10
from .constants import CONTENT_HARD_MATCH_STAGES, ASSOCIATIONS

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        ...

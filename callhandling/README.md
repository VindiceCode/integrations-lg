This is where we house functions for SMS handling.

incomingsms is our most developed function.

This script is designed to process incoming messages, match specific keywords to predefined internal values, and create or update contacts in HubSpot based on the received data. The script uses Azure Functions and the HubSpot API to handle incoming requests and manage contacts.

Key Features:

Keyword Mapping: The script defines a dictionary called CONTENT_HARD_MATCH_STAGES that maps specific keywords to internal values. These mappings are used to categorize incoming messages and determine the appropriate internal value.

Rate Limiting: The script uses the RateLimiter class from the ratelimiter package to control the rate of API requests made to HubSpot, ensuring compliance with their API limits.

HubSpot Integration: The script utilizes the HubSpot API to search for existing contacts, create new contacts, and update contact information. It uses the HubSpot class from the hubspot package to interact with the API.

Error Handling: The script includes various exception handlers to catch and log errors, as well as return appropriate HTTP responses for failed requests.

The main function of the script, main(req: func.HttpRequest), takes an HTTP request as input, processes the request payload, and performs the necessary actions based on the data provided. The function returns an HTTP response with a status code indicating the result of the operation.

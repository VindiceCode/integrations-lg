import logging
import csv
import os
from azure.storage.blob import BlobServiceClient
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    first_name = req.params.get('firstName')
    last_name = req.params.get('lastName')
    phone_number = req.params.get('phoneNumber')

    if not first_name or not last_name or not phone_number:
        return func.HttpResponse(
            "Please provide all required parameters: firstName, lastName, phoneNumber",
            status_code=400
        )

    # Get the connection string from the function app settings
    connection_string = os.environ["urldatavici_storage_account_connection_string"]

    # Create a BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Define the name of your container and the name of the CSV file
    container_name = "urldatavicicontainer"
    csv_file_name = "urldatavici.csv"

    # Create a list to store the captured properties
    captured_properties = [first_name, last_name, phone_number]

    # Convert the captured properties to a CSV string
    csv_data = ','.join(captured_properties)

    # Get a reference to the container
    container_client = blob_service_client.get_container_client(container_name)

    # Upload the CSV data to the blob storage
    blob_client = container_client.get_blob_client(csv_file_name)
    blob_client.upload_blob(csv_data)

    # Return the success response
    return func.HttpResponse("Success")
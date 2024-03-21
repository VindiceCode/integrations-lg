import logging
import csv
import os
from azure.storage.blob import BlobServiceClient
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        first_name = req.params.get('firstName')
        last_name = req.params.get('lastName')
        phone_number = req.params.get('phoneNumber')

        if not first_name or not last_name or not phone_number:
            return func.HttpResponse(
                "Please provide all required parameters: firstName, lastName, phoneNumber",
                status_code=400
            )

        # Get the connection string from the function app settings - 
        connection_string = os.environ["urldatavici_storage_account_connection_string"]

        # Create a BlobServiceClient object
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)

        # Define the name of your container and the name of the CSV file
        container_name = "urldatavicicontainer"
        csv_file_name = "urldatavici.csv"

        # Create a list to store the captured properties
        captured_properties = [first_name, last_name, phone_number]

        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)

        # Define the name of your local file
        local_file_name = "local.csv"

        try:
            # Get a reference to the blob
            blob_client = container_client.get_blob_client(csv_file_name)

            # Download the blob to a local file
            with open(local_file_name, 'wb') as download_file:
                download_file.write(blob_client.download_blob().readall())

            # Append the new data to the local file
            with open(local_file_name, 'a', newline='') as append_file:
                writer = csv.writer(append_file)
            writer.writerow(captured_properties)

            # Upload the local file back to the blob storage
            with open(local_file_name, 'rb') as upload_file:
                blob_client.upload_blob(upload_file, overwrite=True)

        except Exception as e:
            logging.error(str(e))
            return func.HttpResponse("An error occurred while performing blob storage operations", status_code=500)

        # Return the success response
        return func.HttpResponse("Success")
    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse("An error occurred", status_code=500)
Bonzo to HubSpot Integration with Serverless Azure Function App
This project integrates Bonzo with HubSpot using a Serverless Azure Function App. We are using Python 3.11.0 and Azure Functions Core Tools version 4.0.5700.

Prerequisites
--Python 3.11
--Azure Functions Core Tools
--Postman
--GitHub

Setup Instructions :
Create a Python Virtual Environment
python -m venv .venv

Activate the Environment : 
./.venv/Scripts/activate

Install Dependencies : 
pip install -r requirements.txt

Start the Azure Function App : 
In the root project directory:
cd callhandling
func start

Testing the Integration :
You will receive a localhost URL.
Use Postman to send requests to this URL.
Method : POST
Sample payloads are available in the sample data directory under outgoing and incoming sms folders.
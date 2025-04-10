import base64
import requests
from datetime import datetime

def get_mpesa_access_token():
    consumer_key = 'fpe6F7erWAsWay6KJ6q7zu3Qui02I82TPALhG81QUqiELSkB'
    consumer_secret = 'By7y1OTe2zjCrkN7Qt5DxO1RwvP6vX2Cmxi4vrzbD2bBhn8HHR2ytwfsYwRZgmid'
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print("Error: Failed to retrieve access token")
        print(response.json())
        raise Exception("Failed to retrieve access token")

def initiate_payment():
    shortcode = '174379'
    passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    # Generate the password
    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode('utf-8')

    # Get the access token
    access_token = get_mpesa_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": 10,
        "PartyA": "254707098495",
        "PartyB": shortcode,
        "PhoneNumber": "254707098495",
        "CallBackURL": "http://129.151.178.72:8000/mpesa-callback/",
        "AccountReference": "PostXpress",
        "TransactionDesc": "Parcel Payment"
    }

    response = requests.post(api_url, json=payload, headers=headers)
    print(response.json())

if __name__ == "__main__":
    initiate_payment()

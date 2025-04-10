# payments.py
import requests
from django.conf import settings
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

def get_mpesa_access_token():
    """
    Fetches the MPESA access token using consumer key and secret.
    """
    try:
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        # Use HTTPBasicAuth to provide the consumer key and secret
        response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        response_data = response.json()
        
        if response.status_code == 200 and 'access_token' in response_data:
            return response_data['access_token']
        else:
            print("Failed to get access token:", response_data)
            return None
    except Exception as e:
        print(f"Exception occurred while fetching access token: {e}")
        return None


def format_phone_number(phone_number):
    # If the phone number starts with a +254, just remove the + sign
    if phone_number.startswith("+254"):
        return phone_number[1:]  # Return '254XXXXXXXXX' without the '+'

    # Ensure the phone number starts with '254' and remove any leading '0'
    if phone_number.startswith("0"):
        return "254" + phone_number[1:]
    elif not phone_number.startswith("254"):
        return "254" + phone_number
    return phone_number


def initiate_mpesa_payment(phone_number, amount):
    try:
        # Format the phone number correctly
        formatted_phone_number = format_phone_number(phone_number)
        print(f"Formatted phone number: {formatted_phone_number}")  # Log the formatted phone number

        access_token = get_mpesa_access_token()
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

        headers = {"Authorization": f"Bearer {access_token}"}
        
        # BusinessShortCode and key details
        shortcode = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode('utf-8')

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": formatted_phone_number,  # Use formatted phone number
            "PartyB": shortcode,
            "PhoneNumber": formatted_phone_number,  # Use formatted phone number
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": "PostXpress",
            "TransactionDesc": "Parcel Payment"
        }

        print("Request payload:", payload)  # Debugging line
        response = requests.post(api_url, json=payload, headers=headers)
        response_data = response.json()

        # Debugging the response
        print("Response status code:", response.status_code)
        print("Response data:", response_data)

        # Check if the API call was successful
        if response.status_code == 200 and response_data.get('ResponseCode') == '0':
            return response_data
        else:
            # Log the error response
            print(f"Error response from MPESA API: {response_data}")
            return {"errorMessage": response_data.get('errorMessage', "Payment failed. Please check your details.")}
    except Exception as e:
        print(f"Exception occurred: {e}")
        return {"errorMessage": "An error occurred while processing the payment. Please try again."}

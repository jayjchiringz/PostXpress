import africastalking
from django.conf import settings

# Initialize Africastalking SDK
username = settings.AFRICASTALKING_USERNAME
api_key = settings.AFRICASTALKING_API_KEY
africastalking.initialize(username, api_key)

sms = africastalking.SMS

def send_sms(to, message):
    """
    Send an SMS message using Africastalking.
    :param to: List of phone numbers (e.g., ['+2547XXXXXXXX'])
    :param message: The message to be sent
    """
    # Replace all numbers with the sandbox number
    sandbox_number = "+254711082000"
    to = [sandbox_number]

    try:
        response = sms.send(message, to)
        print("SMS sent successfully:", response)
        return response

    except Exception as e:
        print(f"Failed to send SMS: {e}")
        return None


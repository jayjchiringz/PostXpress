import os
import django
import africastalking
import sys
from django.conf import settings

# Add the project base directory to sys.path
sys.path.append('/home/opc/PostXpress/PostXpress')  # Adjust this path to your project

# Set the environment variable for the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PostXpress.settings')

# Initialize Django settings
django.setup()

# Initialize Africa's Talking
username = settings.AFRICASTALKING_USERNAME 
api_key = settings.AFRICASTALKING_API_KEY

# Debugging: Print the values to ensure they are correctly initialized
print(f"Username: {repr(username)}")  # Print username to see its exact representation
print(f"API Key: {repr(api_key[:6])}...")  # Print part of API key for security

# Make sure the values are strings
if not isinstance(username, str):
    print(f"Error: username is not a string, but {type(username)}")
    raise ValueError("username must be a string.")
    
if not isinstance(api_key, str):
    print(f"Error: api_key is not a string, but {type(api_key)}")
    raise ValueError("api_key must be a string.")

# Initialize Africa's Talking
africastalking.initialize(username, api_key)

sms = africastalking.SMS


def send_test_sms():
    recipients = ['+254711082000']  # Replace with the sandbox phone number or a real number for production
    message = "This is a test message from PostXpress using Africastalking!"

    try:
        # Send SMS
        response = sms.send(message, recipients)
        print("SMS sent successfully:", response)

    except Exception as e:
        print(f"Failed to send SMS: {e}")

if __name__ == '__main__':
    send_test_sms()

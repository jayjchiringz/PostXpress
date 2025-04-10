import os
from flask import Flask, request, Response
from send_sms import SMSClient

app = Flask(__name__)

# Create an instance of SMSClient
sms_client = SMSClient()

# Route for incoming messages
@app.route('/incoming-messages', methods=['POST'])
def incoming_messages():
    data = request.get_json(force=True)
    print(f'Incoming message...\n{data}')
    # Additional logic to process incoming messages can go here
    return Response(status=200)

# Route for delivery reports
@app.route('/delivery-reports', methods=['POST'])
def delivery_reports():
    data = request.get_json(force=True)
    print(f'Delivery report response...\n{data}')
    # Additional logic to process delivery reports can go here
    return Response(status=200)

if __name__ == "__main__":
    # Test sending an SMS when the app starts
    recipients = ["+254711111111"]  # Replace with actual phone numbers
    message = "Hello, AT Ninja!"
    sender_id = "3991"  # Optional, use a short code or alphanumeric sender ID if available

    # Sending the SMS using the SMSClient instance
    sms_client.send(recipients, message, sender_id)
    
    # Run the Flask app
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))

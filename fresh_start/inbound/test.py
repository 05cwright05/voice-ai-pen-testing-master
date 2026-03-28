# Download the helper library from https://www.twilio.com/docs/python/install
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env
from twilio.rest import Client

# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ["TWILIO_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

call = client.calls.create(
    twiml="<Response><Say>Ahoy, World it is I gangington maximus</Say></Response>",
    to="+18126298894",
    from_="+18125058284",
)

print(call.sid)
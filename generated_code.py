import os
import requests
import datetime
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve API key from environment variables
SKYFIRE_API_KEY = os.getenv('SKYFIRE_API_KEY')

# Check if SKYFIRE_API_KEY exists
if not SKYFIRE_API_KEY:
    raise EnvironmentError("SKYFIRE_API_KEY not found in environment variables.")

# Define headers for Skyfire API requests
headers = {
    'skyfire-api-key': SKYFIRE_API_KEY,
    'Content-Type': 'application/json'
}

def create_skyfire_token(buyer_tag, token_amount, seller_service_id):
    """
    Creates a KYA+PAY token with Skyfire.
    
    :param buyer_tag: Unique identifier for the buyer
    :param token_amount: Amount for the token
    :param seller_service_id: ID of the seller service
    :return: Token string if successful, None otherwise
    """
    try:
        # Define the payload for token creation
        payload = {
            'type': 'kya+pay',
            'buyerTag': buyer_tag,
            'tokenAmount': token_amount,
            'sellerServiceId': seller_service_id,
            'expiresAt': int((datetime.datetime.now() + datetime.timedelta(hours=24)).timestamp())
        }

        # Make the request to create the token
        response = requests.post('https://api.skyfire.xyz/api/v1/tokens', headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Retrieve the created token from the response
        token_data = response.json()
        return token_data.get('token')

    except requests.exceptions.RequestException as e:
        print(f"Error creating token: {e}")
        return None

def charge_skyfire_token(token, charge_amount):
    """
    Charges a Skyfire token.
    
    :param token: The token string to be charged
    :param charge_amount: The amount to charge from the token
    :return: Result of the charge operation
    """
    try:
        # Define the payload for charging the token
        charge_payload = {
            'token': token,
            'chargeAmount': charge_amount
        }

        # Make the request to charge the token
        charge_response = requests.post('https://api.skyfire.xyz/api/v1/tokens/charge', headers=headers, json=charge_payload)
        charge_response.raise_for_status()  # Raise HTTPError for bad responses

        # Retrieve the charge result from the response
        charge_result = charge_response.json()
        return charge_result

    except requests.exceptions.RequestException as e:
        print(f"Error charging token: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    buyer_tag = 'your_unique_buyer_tag'
    token_amount = '0.005'
    seller_service_id = '350d433d-6ed4-4482-bcfc-14b7da807f7z'

    # Create a KYA+PAY token
    token = create_skyfire_token(buyer_tag, token_amount, seller_service_id)
    if token:
        print(f"Successfully created token: {token}")
        
        # Charge the token
        charge_result = charge_skyfire_token(token, token_amount)
        if charge_result:
            print(f"Successfully charged token. Charge Result: {charge_result}")
    else:
        print("Failed to create token. Exiting script.")
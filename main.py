import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip = response.json().get('ip')
        return ip
    except requests.RequestException as e:
        logging.error(f"Error fetching IP address: {e}")
        return None

if __name__ == "__main__":
    ip_address = get_public_ip()
    if ip_address:
        logging.info(f"My public IP address is: {ip_address}")
    else:
        logging.error("Could not fetch the public IP address.")
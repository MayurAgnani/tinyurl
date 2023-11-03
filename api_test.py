import requests
import json
import datetime
import calendar

# Base URL of your Flask application
base_url = "http://localhost:5000"

# Function to create a short URL
def create_short_url(long_url):
    
    endpoint = f"{base_url}/tiny"
    data = {"long_url": long_url}
    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=json.dumps(data), headers=headers)
    return response

# Function to create a short URL
def create_short_url_with_expiration(long_url):
    
    endpoint = f"{base_url}/tiny"
    date = datetime.datetime.now(datetime.UTC)
    utc_time = calendar.timegm(date.utctimetuple())
    data = {"long_url": long_url,"expiration_time":utc_time}
    headers = {"Content-Type": "application/json"}
    response = requests.post(endpoint, data=json.dumps(data), headers=headers)
    return response


# Function to access the long URL
def access_long_url(short_url):
    
    endpoint = f"{base_url}/tiny/{short_url}"
    response = requests.get(endpoint)
    print(response.json())
    return response

# Function to delete a short URL
def delete_short_url(short_url):
    
    endpoint = f"{base_url}/tiny/{short_url}"
    response = requests.delete(endpoint)
    print(response)
    return response

# Function to retrieve URL statistics
def get_url_stats(short_url):
    
    endpoint = f"{base_url}/tiny/stats/{short_url}"
    response = requests.get(endpoint)
    print(response.json())
    return response

if __name__ == "__main__":
    # Test creating a short URL
    
    long_url = "https://www.tinyurlexample.com"
    create_response = create_short_url(long_url)

    # Extract the short URL from the response
    short_url = create_response.json().get("short_url")
 
    access_long_url(short_url)
    
    
    get_url_stats(short_url)
    
    
    long_url_to_expired = "https://www.tinyurlexampletobexpired.com"
    expired_url_response = create_short_url_with_expiration(long_url_to_expired)
   
    print(expired_url_response.json())
 
    
 
 

   
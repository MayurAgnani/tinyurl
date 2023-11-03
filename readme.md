# URL Shortener Readme

  

This is a URL shortener application built using Flask, MongoDB, and Redis. The application allows you to shorten long URLs, access the original URLs using short URLs, and retrieve statistics about the access counts. Below is a guide on how to set up and use this application.

Hashes timestamp+url+random 4 digit number as md5 takes 7 characters, it can store 250 mn urls. For new shorts urls it checks if the hash alread exists.

Since it's a read heave system we cache the last frequent 100 queries in redis cache.

 
## Getting Started

  

These instructions will help you set up and run the URL shortener application on your local machine.

  

### Prerequisites

  

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.

  

### Installation

  

1. Clone this repository to your local machine.

  

2. Build the Docker containers by running the following command in the project's root directory:

  

```bash

docker-compose up --build

```

  

This command will set up containers for the Flask application, MongoDB, and Redis.

  

3. Once the containers are up and running, you can access the URL shortener at [http://localhost:5000](http://localhost:5000).

  
  Sure, here's a REST API documentation for the Flask application you provided:

## URL Shortener API Documentation

This API allows you to create short URLs, retrieve long URLs, delete short URLs, and get URL statistics. It is a URL shortening service that uses MongoDB for storing URL data and Redis for caching.

### Base URL
The base URL of the API is: `http://localhost:5000`

### Endpoints

#### 1. Home Page
- **Endpoint:** `/`
- **Method:** GET
- **Description:** Display the home page of the URL Shortener.
- **Response:** A simple message indicating the home page of the application.

#### 2. Create a Short URL
- **Endpoint:** `/tiny`
- **Method:** POST
- **Description:** Create a short URL for a given long URL and store it in the database.
- **Request Payload:** JSON object with a single field `"long_url"` representing the long URL to be shortened. An optional field `"expiration_time"` can be provided to set an expiration time for the short URL.
  Example Request:
  ```json
  {
    "long_url": "https://www.example.com/very-long-url-that-needs-shortening",
    "expiration_time": 1675041600
  }
  ```
- **Response:** JSON object with a status and the generated short URL.
  Example Response:
  ```json
  {
    "status": true,
    "message": "Short URL created",
    "short_url": "http://localhost:5000/tiny/abc123"
  }
  ```

#### 3. Retrieve the Long URL
- **Endpoint:** `/tiny/{short_url}`
- **Method:** GET
- **Description:** Retrieve the long URL associated with a short URL.
- **Response:** JSON object with a status and the long URL. If the short URL has expired, it returns an error message.
  Example Response:
  ```json
  {
    "status": true,
    "long_url": "https://www.example.com/original-long-url"
  }
  ```

#### 4. Delete a Short URL
- **Endpoint:** `/tiny/{short_url}`
- **Method:** DELETE
- **Description:** Delete a short URL from the database.
- **Response:** JSON object with a status indicating whether the short URL was successfully deleted or not.

#### 5. Retrieve URL Statistics
- **Endpoint:** `/tiny/stats/{short_url}`
- **Method:** GET
- **Description:** Retrieve statistics for a short URL, including the number of clicks within the last 24 hours, the last 7 days, and all time.
- **Response:** JSON object with a status and the access counts.
  Example Response:
  ```json
  {
    "status": true,
    "24_hr_count": 10,
    "7_day_count": 100,
    "all_time_count": 1000
  }
  ```

### Usage Examples
You can use the provided Python script to interact with these endpoints. Make POST requests to create short URLs, GET requests to retrieve long URLs or statistics, and DELETE requests to delete short URLs.

Feel free to add any additional details or modify the documentation as needed for your specific use case.


  

## DB schema

  

```
message = {

"creation_time": time,

"long_url": string,

"short_url": string,

"24_hr_count": Number,

"7_day_count": Number,

"all_time_count": Number,

"last_access_time": time,

"expiration_time": time,

}
```
with short_url and long_url as index

  

## Using the Python Client

  

In the `api_test.py` script, you can find functions to interact with the URL shortener:

  

- `create_short_url(long_url)`: Create a short URL.

- `create_short_url_with_expiration(long_url)`: Create a short URL.

- `access_long_url(short_url)`: Access the original long URL.

- `delete_short_url(short_url)`: Delete a short URL.

- `get_url_stats(short_url)`: Retrieve access statistics for a short URL.

  

You can run this script to test the URL shortener and interact with it programmatically.

  

```bash

python api_test.py

```

  

## Troubleshooting

  

If you encounter any issues or errors during setup or while using the application, please check the logs in the `tinyurl.log` file, which is generated by the Flask application. It can provide valuable information for debugging.

  

## Built With

  

- [Flask](https://flask.palletsprojects.com/) - A micro web framework for Python.

- [MongoDB](https://www.mongodb.com/) - A NoSQL database for storing URL data.

- [Redis](https://redis.io/) - An in-memory data store for caching short URLs.

  

## TODO

- Url validation

- Caching on access pattern

## Scale

- Add multiple instances of the server and DB

- Potwntially a Key Generation service can be used and a certain number of keys can be cached

-  - Load Balancing

-  - Sharding the urls

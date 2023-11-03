import logging
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
import redis
import calendar
import datetime
from utils import URLStats, ShortURL

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration settings
app.config[
    "MONGO_URI"
] = "mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority"
app.config["REDIS_HOST"] = "redis"
app.config["REDIS_PORT"] = 6379
app.config["REDIS_CACHE_KEY_PREFIX"] = "url_cache_"

mongo = PyMongo(app)
client = MongoClient(
    "mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority"
)
db = client["urldb"]
url_collection = db["urldb"]
redis_cache = redis.Redis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"])


@app.route("/")
def home():
    """
    Display the home page of the URL Shortener.

    Returns:
        str: A message indicating the home page of the application.
    """
    return "Home Page of URL Shortener"

@app.route("/tiny", methods=["POST"])
def shorten_url():
    """
    Shorten a long URL and store it in the database.

    This endpoint takes a long URL as input and generates a short URL hash for it.
    The generated short URL is then stored in the database for access.

    Returns:
        JSON: A response indicating the status and the generated short URL.
    """
    data = request.get_json()
    if "long_url" not in data:
        return jsonify({"status": False, "error": "Missing Long URL"}), 400

    long_url = data["long_url"]
    date = datetime.datetime.utcnow()
    utc_time = calendar.timegm(date.utctimetuple())
    try:
        document = url_collection.find_one({"long_url": long_url})

        if document:
            expiration_time = document.get("expiration_time", None)
            if (expiration_time is None) or (
                expiration_time and int(expiration_time) > int(utc_time)
            ):
                return jsonify(
                    {
                        "status": True,
                        "message": "Short URL already exists",
                        "short_url": document["short_url"],
                    }
                )
            else:
                result = url_collection.delete_one({"short_url": document["short_url"]})
                if result.deleted_count == 1:
                    logging.info("Expired Short URL deleted: %s", document["short_url"])
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))

    short_url_hash = ShortURL.generate_short_url(long_url)

    while url_collection.find_one({"short_url": short_url_hash}):
        short_url_hash = ShortURL.generate_short_url(long_url)

    expiration_time = data.get("expiration_time", None)
    if expiration_time:
        expiration_time = int(expiration_time)

    message = {
        "creation_time": utc_time,
        "long_url": long_url,
        "short_url": short_url_hash,
        "24_hr_count": 0,
        "7_day_count": 0,
        "all_time_count": 0,
        "last_access_time": utc_time,
        "expiration_time": expiration_time,
    }
    try:
        url_collection.insert_one(message)
        logging.info("Short URL created: %s", short_url_hash)
    except Exception as e:
        logging.error(
            "An error occurred while inserting data into the database: %s", str(e)
        )

    short_url = "http://localhost:5000/tiny/" + short_url_hash
    return jsonify(
        {"status": True, "message": "Short URL created", "short_url": short_url}
    )

@app.route("/tiny/<string:short_url>")
def get_long_url(short_url):
    """
    Retrieve the long URL associated with a short URL.

    This endpoint retrieves the long URL associated with a given short URL.
    It checks both a Redis cache and the database for the URL.

    Returns:
        JSON: A response indicating the status and the long URL.
    """
    try:
        date = datetime.datetime.utcnow()
        current_time = calendar.timegm(date.utctimetuple())
        # Check the Redis cache for the short URL
        cached_long_url = redis_cache.get(short_url)
        if cached_long_url:
            # URL found in the cache, return it
            logging.info("Serving from cache: %s", short_url)
            URLStats.increment_counts(short_url, current_time, url_collection)
            return jsonify({"status": True, "long_url": cached_long_url.decode()}), 200

        # URL not found in the cache, proceed to check the database
        document = url_collection.find_one({"short_url": short_url})
        if document:
            # Update the Redis cache with the accessed short URL
            redis_cache.set(short_url, document["long_url"])
            # Keep only the latest 100 URLs in the cache
            cached_urls = redis_cache.keys("*")
            if len(cached_urls) > 100:
                oldest_url = min(cached_urls, key=redis_cache.get)
                redis_cache.delete(oldest_url)

           
            expiration_time = document.get("expiration_time", None)
            logging.info(expiration_time)
            if expiration_time and int(current_time) > int(expiration_time):
                logging.info("expiration_time")
                logging.info(expiration_time)
                logging.info("current_time")
                logging.info(current_time)
                return jsonify({"status": False, "error": "Short URL has expired"}), 400

            URLStats.increment_counts(short_url, current_time, url_collection)
            long_url = document["long_url"]
            logging.info("Short URL accessed: %s", short_url)
            return jsonify({"status": True, "long_url": long_url}), 200
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)

@app.route("/tiny/<string:short_url>", methods=["DELETE"])
def delete_short_url(short_url):
    """
    Delete a short URL from the database and cache (if it exists in the cache).

    This endpoint allows the deletion of a short URL from the database and removes it from the cache if it exists in the cache.

    Returns:
        JSON: A response indicating the status of the deletion operation.
    """
    try:
        # Remove the short URL from the database
        result = url_collection.delete_one({"short_url": short_url})
        if result.deleted_count == 1:
            logging.info("Short URL deleted: %s", short_url)
            # Check if the short URL exists in the cache and remove it
            if redis_cache.exists(short_url):
                redis_cache.delete(short_url)
            return jsonify({"status": True, "message": "Short URL deleted"})
    except Exception as e:
        logging.error("An error occurred while deleting the short URL: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)


@app.route("/tiny/stats/<string:short_url>")
def get_url_stats(short_url):
    """
    Retrieve statistics for a short URL.

    This endpoint retrieves statistics for a given short URL, including access counts.

    Returns:
        JSON: A response indicating the status and the access counts.
    """
    try:
        document = url_collection.find_one({"short_url": short_url})
        if document:
            logging.info("Stats accessed for: %s", short_url)
            return jsonify(
                {
                    "status": True,
                    "24_hr_count": document["24_hr_count"],
                    "7_day_count": document["7_day_count"],
                    "all_time_count": document["all_time_count"],
                }
            )
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)

if __name__ == "__main__":
    logging.basicConfig(filename="tinyurl.log", level=logging.INFO)
    app.run()

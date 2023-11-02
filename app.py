import logging
from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
import time
import redis
import hashlib
import random
import calendar
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Configuration settings
app.config['MONGO_URI'] = "mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority"
app.config['REDIS_HOST'] = 'redis'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_CACHE_KEY_PREFIX'] = 'url_cache_'

mongo = PyMongo(app)
client = MongoClient('mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority')
db = client['urldb']
url_collection = db['urldb']
redis_cache = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'])

class ShortURL:
    @staticmethod
    def generate_short_url(long_url):
        number = random.randint(1000, 9999)
        padded_long_url = str(time.time()) + long_url + str(number)
        result = hashlib.md5(padded_long_url.encode())
        short_url_hash = str(result.hexdigest())[:7]
        return short_url_hash

class URLStats:
    @staticmethod
    def increment_counts(short_url, current_time, url_collection):
        try:
            last_access_time = url_collection.find_one({"short_url": short_url})['last_access_time']
            if current_time - last_access_time <= 24 * 60 * 60:
                url_collection.update_one({"short_url": short_url}, {"$inc": {"24_hr_count": 1}})
            if current_time - last_access_time <= 7 * 24 * 60 * 60:
                url_collection.update_one({"short_url": short_url}, {"$inc": {"7_day_count": 1}})
            url_collection.update_one({"short_url": short_url}, {"$inc": {"all_time_count": 1}})
            url_collection.update_one({"short_url": short_url}, {"$set": {"last_access_time": current_time}})
        except Exception as e:
            logging.error("An error occurred while updating URL stats: %s", str(e))

@app.route("/")
def home():
    return "Home Page of URL Shortener"

@app.route("/tiny", methods=["POST"])
def shorten_url():
    data = request.get_json()
    if "long_url" not in data:
        return jsonify({"status": False, "error": "Missing Long URL"}), 400

    long_url = data["long_url"]
    date = datetime.datetime.utcnow()
    utc_time = calendar.timegm(date.utctimetuple())
    try:
        document = url_collection.find_one({"long_url": long_url})

        if document:
           
            expiration_time = data.get("expiration_time", None)
            if expiration_time and expiration_time < utc_time:
                return jsonify({"status": True, "message": "Short URL already exists", "short_url": short_url})
            else:
                result = url_collection.delete_one({"short_url": short_url})
                if result.deleted_count == 1:
                    logging.info("Expired Short URL deleted: %s", short_url)
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))

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
        "expiration_time": expiration_time
    }
    try:
        url_collection.insert_one(message)
        logging.info("Short URL created: %s", short_url_hash)
    except Exception as e:
        logging.error("An error occurred while inserting data into the database: %s", str(e))

    short_url = "http://localhost:5000/tiny/" + short_url_hash
    return jsonify({"status": True, "message": "Short URL created", "short_url": short_url})

@app.route("/tiny/<string:short_url>")
def get_long_url(short_url):
    try:
        document = url_collection.find_one({"short_url": short_url})
        if document:
            date = datetime.datetime.utcnow()
            current_time = calendar.timegm(date.utctimetuple())
            expiration_time = document.get("expiration_time", None)
            if expiration_time and int(current_time) > int(expiration_time):
                return jsonify({"status": False, "error": "Short URL has expired"}), 400

            URLStats.increment_counts(short_url, current_time, url_collection)
            long_url = document["long_url"]
            logging.info("Short URL accessed: %s", short_url)
            return jsonify({"status": True, "long_url": long_url}), 302
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)

@app.route("/tiny/<string:short_url>", methods=["DELETE"])
def delete_short_url(short_url):
    try:
        result = url_collection.delete_one({"short_url": short_url})
        if result.deleted_count == 1:
            logging.info("Short URL deleted: %s", short_url)
            return jsonify({"status": True, "message": "Short URL deleted"})
    except Exception as e:
        logging.error("An error occurred while deleting the short URL: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)

@app.route("/tiny/stats/<string:short_url>")
def get_url_stats(short_url):
    try:
        document = url_collection.find_one({"short_url": short_url})
        if document:
            logging.info("Stats accessed for: %s", short_url)
            return jsonify({
                "status": True,
                "24_hr_count": document["24_hr_count"],
                "7_day_count": document["7_day_count"],
                "all_time_count": document["all_time_count"]
            })
    except Exception as e:
        logging.error("An error occurred while accessing the database: %s", str(e))
    return jsonify({"status": False, "error": "Short URL not found"}, 404)

if __name__ == "__main__":
    logging.basicConfig(filename='tinyurl.log', level=logging.INFO)
    app.run()

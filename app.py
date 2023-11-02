from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo import MongoClient
import time;
import redis
import hashlib
import random



app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority"
app.config['REDIS_HOST'] = 'redis'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_CACHE_KEY_PREFIX'] = 'url_cache_'
mongo = PyMongo(app)
client = MongoClient('mongodb+srv://cloudflare:cloudflare@cluster0.d7w8l8l.mongodb.net/?retryWrites=true&w=majority')
db = client['urldb']
url_collection = db['urldb']
chat_collection = db['urldb']
redis_cache = redis.Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'])



@app.route("/")
def home():
    return "Home Page of url shrotner"


@app.route("/tiny", methods=["POST"])
def shorten_url():
    data = request.get_json()
    if "long_url" not in data:
        return jsonify({"status": False, "error": "Missing Long Url"}), 400
    
    expiration_date = data.get("expiration_date", None)

    long_url = data["long_url"]
    
    document = url_collection.find_one({"long_url": long_url})
    
    if document:
        
        short_url = "http://localhost:5000/tiny/" + document["short_url"]
    
        return jsonify({"status": True, "message": "Short URL already exists", "short_url": short_url})

    short_url_hash = generate_short_url(long_url)

    message = {"creation_time":time.time(), "long_url":long_url, "short_url":short_url_hash, "24_hr_count":0, "7_day_count":0, "all_time_count":0,"last_access_time":time.time(),"expiration_time":expiration_date}
    url_collection.insert_one(message)
    
    short_url = "http://localhost:5000/tiny/" + short_url_hash

    return jsonify({"status": True, "message": "Short URL created", "short_url": short_url})



@app.route("/tiny/<string:short_url>")
def get_long_url(short_url):
    # Query the MongoDB collection for the matching short URL
    document = url_collection.find_one({"short_url": short_url})

    if document:
        # Get the current time
        current_time = time.time()
        
        expiration_date = document.get("expiration_date",None)
        if expiration_date and current_time > expiration_date:
            # Handle expired URL
            return jsonify({"status": False, "error": "Short URL has expired"}), 400

        # Get the last access time from the document or set it to the current time
        last_access_time = document.get("last_access_time", current_time)

        # Check if the last access time is within the last 24 hours
        if current_time - last_access_time <= 24 * 60 * 60:
            # Increment the 24-hour count
            url_collection.update_one({"short_url": short_url}, {"$inc": {"24_hr_count": 1}})

        # Check if the last access time is within the last 7 days
        if current_time - last_access_time <= 7 * 24 * 60 * 60:
            # Increment the 7-day count
            url_collection.update_one({"short_url": short_url}, {"$inc": {"7_day_count": 1}})
            
        url_collection.update_one({"short_url": short_url}, {"$inc": {"all_time_count": 1}})

        # Update the last access time to the current time
        url_collection.update_one({"short_url": short_url}, {"$set": {"last_access_time": current_time}})

        long_url = document["long_url"]
        return jsonify({"status": True, "long_url": long_url}), 302
    else:
        return jsonify({"status": False, "error": "Short URL not found"}, 404)



@app.route("/tiny/<string:short_url>", methods=["DELETE"])
def delete_short_url(short_url):
    # Delete the document with the matching short URL from the MongoDB collection
    result = url_collection.delete_one({"short_url": short_url})

    if result.deleted_count == 1:
        return jsonify({"status": True, "message": "Short URL deleted"})
    else:
        return jsonify({"status": False, "error": "Short URL not found"}), 404
    
    
@app.route("/tiny/stats/<string:short_url>")
def get_url_stats(short_url):
    # Query the MongoDB collection for the matching short URL
    document = url_collection.find_one({"short_url": short_url})

    if document:
        return jsonify({"status": True, "24_hr_count": document["24_hr_count"], "7_day_count": document["7_day_count"], "all_time_count": document["all_time_count"]})
    else:
        return jsonify({"status": False, "error": "Short URL not found"}, 404)


def generate_short_url(long_url):
    number = random.randint(1000, 9999)
    padded_long_url = str(time.time()) + long_url + str(number)
    result = hashlib.md5(padded_long_url.encode())
    short_url_hash = str(result.hexdigest())[:7]
    return short_url_hash


if __name__ == "__main__":
    app.run()


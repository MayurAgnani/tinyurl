import hashlib
import random
import logging
import time

class ShortURL:
    @staticmethod
    def generate_short_url(long_url):
        """
        Generate a short URL hash for a given long URL.

        Args:
            long_url (str): The long URL to be shortened.

        Returns:
            str: A 7-character short URL hash.
        """
        number = random.randint(1000, 9999)
        padded_long_url = str(time.time()) + long_url + str(number)
        result = hashlib.md5(padded_long_url.encode())
        short_url_hash = str(result.hexdigest())[:7]
        return short_url_hash

class URLStats:
    @staticmethod
    def increment_counts(short_url, current_time, url_collection):
        """
        Increment access counts for a given short URL in the database.

        Args:
            short_url (str): The short URL.
            current_time (int): The current time in seconds since the epoch.
            url_collection: The MongoDB collection for URL statistics.

        This function updates the access counts for a short URL based on time intervals.
        """
        try:
            last_access_time = url_collection.find_one({"short_url": short_url})[
                "last_access_time"
            ]
            if current_time - last_access_time <= 24 * 60 * 60:
                url_collection.update_one(
                    {"short_url": short_url}, {"$inc": {"24_hr_count": 1}}
                )
            if current_time - last_access_time <= 7 * 24 * 60 * 60:
                url_collection.update_one(
                    {"short_url": short_url}, {"$inc": {"7_day_count": 1}}
                )
            url_collection.update_one(
                {"short_url": short_url}, {"$inc": {"all_time_count": 1}}
            )
            url_collection.update_one(
                {"short_url": short_url}, {"$set": {"last_access_time": current_time}}
            )
        except Exception as e:
            logging.error("An error occurred while updating URL stats: %s", str(e))
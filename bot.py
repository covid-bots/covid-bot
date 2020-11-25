from instabot import Bot as Instabot
import json
import requests

from exceptions import *


class CovidStatsInstagramBot:

    COUNTRY = "israel"
    API_BASE_URL = "https://api.covid19api.com/dayone/country/"
    SOCIALMEDIA_INFO_PATH = "login-info.json"

    @classmethod
    def upload_image(cls, img_path: str, caption: str = None):
        """ Recives a path to an image, and uploads the given image to the
        Instagram account saved in the login info file.
        """

        # Load json from the login info file
        with open(cls.SOCIALMEDIA_INFO_PATH) as f:
            login_info = json.load(f)

        # Get Instagram username and password
        insta_username = login_info["instagram"]["username"]
        insta_password = login_info["instagram"]["password"]

        # Load the Instagram bot
        bot = Instabot()
        bot.login(username=insta_username, password=insta_password)

        # upload the given photo
        bot.upload_photo(img_path, caption=caption)

    @classmethod
    def get_stats(cls):
        """ Returns the Covid data from covid19api.com """

        # Make a request to the api
        url = cls.API_BASE_URL + cls.COUNTRY
        response = requests.get(url=url)

        # Check if data loaded correctly
        if response.status_code != 200:
            raise requestAPIError(
                f"{url}:\nResponse status {response.status_code}.")

        return response.json()

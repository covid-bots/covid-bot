from instabot import Bot as Instabot
import json
import requests
from datetime import datetime
from os import remove, environ
import logging
from logging.handlers import TimedRotatingFileHandler

from exceptions import *
from api import Covid19API
from painter import ImageGenerator


formatter = logging.Formatter("[%(asctime)s] (%(levelname)s) | %(message)s")

file_handler = TimedRotatingFileHandler(
    "main.log", when="midnight", backupCount=3)
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


class CovidStatsInstagramBot:

    COUNTRY = "israel"
    COMPARE_X_DAYS = 60

    BIG_TITLE = "םישדח םילוח"
    MIDDLE_TITLES = ["םיתמ", "תעכ םילוח", "ומילחה"]
    SUBTITLE_TEMPLATE = "לומתאמ %n%="
    SUBTITLE_NO_CHANGE = "יוניש אלל"
    GRAPH_TITLE = "םינורחאה םיישדוחב ,םויב םישדח םילוח :ףרג"
    BOTTOM_TEXT_TEMPLATE = "%d | @covid_israel | ישילש דצ ידי לע קפוסמו ,ימשר וניא עדימה"
    CAPTION_TEMPLATE = "מצב נגיף הקורונה בישראל - %d 🦠😷🏥\nשמירה על ההנחיות מצילה חיים. רק כך נוכל לחזור לשגרה! 🙂"

    TEMP_IMAGE_NAME = "TEMPIMG.jpg"

    @classmethod
    def upload_image(cls, img_path: str, caption: str = None):
        """ Recives a path to an image, and uploads the given image to the
        Instagram account saved in the login info file.
        """

        # Get Instagram username and password
        insta_username = environ.get("COVID_INSTAGRAM_USERNAME")
        insta_password = environ.get("COVID_INSTAGRAM_PASSWORD")

        if (not insta_username) or (not insta_password):
            raise ValueError(
                "Environment variables not found.\nPlease set the environment variables 'COVID_INSTAGRAM_USERNAME' and 'COVID_INSTAGRAM_PASSWORD'."
            )

        # Load the Instagram bot
        bot = Instabot()
        bot.login(username=insta_username, password=insta_password)

        # upload the given photo
        bot.upload_photo(img_path, caption=caption, options={"rename": False})

    @classmethod
    def __generate_delta_subtitle(cls, amount: int):

        if amount == 0:
            return cls.SUBTITLE_NO_CHANGE

        string = cls.SUBTITLE_TEMPLATE.replace("%n", str(abs(amount)))

        if amount > 0:
            return string.replace("%=", "+")
        return string.replace("%=", "-")

    @classmethod
    def get_image(cls):
        """ Generates the Covid stats image, and saves it in the given
        path. """

        # Get data from api
        data = Covid19API.get_stats(
            cls.COUNTRY, last_x_days=cls.COMPARE_X_DAYS+1)

        # Get number of new cases today
        today_diff = data.compare_to_yesterday()
        new_cases = today_diff.confirmed_diff

        # Generate the base image
        img = ImageGenerator.generate_base_img(new_cases)
        ImageGenerator.add_big_title(img, cls.BIG_TITLE, str(new_cases))

        # Add small information titles
        today = data.get_today()
        mid_titles = cls.MIDDLE_TITLES
        mid_values = [str(x)
                      for x in [today.deaths, today.active_cases, today.recovered_cases]]
        mid_subtitles = [cls.__generate_delta_subtitle(n)
                         for n in [today_diff.deaths_diff, today_diff.active_diff, today_diff.recovered_diff]]
        ImageGenerator.add_small_titles_row(
            img, mid_titles, mid_values, mid_subtitles)

        # Add graph
        cases_a_day = data.get_cases_a_day_list()
        img = ImageGenerator.add_graph(
            cases_a_day, img, title=cls.GRAPH_TITLE)

        # Add bottom text
        date = datetime.today()
        date_str = date.strftime("%d/%m/%Y")
        ImageGenerator.add_bottom_test(
            img, cls.BOTTOM_TEXT_TEMPLATE.replace("%d", date_str))

        return img

    @classmethod
    def get_caption(cls):
        """ Generate caption for the Instagram post. """

        date = datetime.today()
        date_str = date.strftime("%d/%m/%Y")
        return cls.CAPTION_TEMPLATE.replace("%d", date_str)

    @classmethod
    def genereate_and_upload(cls):
        """ Generate a new image, and upload it to Instagram. """

        # Generate and save the covid image.
        img = CovidStatsInstagramBot.get_image().convert("RGB")
        img.save(cls.TEMP_IMAGE_NAME)

        # Upload the image to instagram
        caption = CovidStatsInstagramBot.get_caption()
        CovidStatsInstagramBot.upload_image(cls.TEMP_IMAGE_NAME, caption)

        remove(cls.TEMP_IMAGE_NAME)

    @classmethod
    def upload_if_new_data(cls):

        logger.info("Checking for new information...")

        data = Covid19API.get_stats(cls.COUNTRY, last_x_days=1)
        json_data = {"date": data.get_today().date}

        if not DataStorageManager.diff_from_saved_data(json_data):
            # If there is no new data...
            logger.info("No new data found.")
            return

        # If there is new data
        logger.info("New data found, generating and uploading image.")
        cls.genereate_and_upload()
        DataStorageManager.save_data(json_data)


class DataStorageManager:

    DATA_FILE = "PREV_DATA.json"

    @classmethod
    def save_data(cls, data: dict):
        """ Saves the given data dict as a json file,
        in the file specified with the `DATA_FILE` property.
        """

        with open(cls.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    @classmethod
    def load_data(cls):
        """ Returns the data in the file specified with the `DATA_FILE`
        property. """

        try:
            with open(cls.DATA_FILE) as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    @classmethod
    def diff_from_saved_data(cls, data: dict):
        """ Returns a boolean value. `True` if the given data is different
        and does not match the saved data (or if there is no saved data),
        and `False` if the saved data matches the given data. """

        saved_data = cls.load_data()
        return not saved_data == data


if __name__ == "__main__":
    CovidStatsInstagramBot.upload_if_new_data()

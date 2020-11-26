from instabot import Bot as Instabot
import json
import requests
from datetime import datetime

from exceptions import *
from api import Covid19API
from painter import ImageGenerator


class CovidStatsInstagramBot:

    COUNTRY = "israel"
    COMPARE_X_DAYS = 60

    API_BASE_URL = "https://api.covid19api.com/dayone/country/"
    SOCIALMEDIA_INFO_PATH = "logininfo.json"

    BIG_TITLE = "םישדח םילוח"
    MIDDLE_TITLES = ["םיתמ", "תעכ םילוח", "ומילחה"]
    SUBTITLE_TEMPLATE = "לומתאמ %n%="
    SUBTITLE_NO_CHANGE = "יוניש אלל"
    GRAPH_TITLE = "םינורחאה םיישדוחב ,םויב םישדח םילוח :ףרג"
    BOTTOM_TEXT_TEMPLATE = "%d | @covid_israel | ישילש דצ ידי לע קפוסמו ,ימשר וניא עדימה"

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
    def __generate_delta_subtitle(cls, amount: int):

        if amount == 0:
            return cls.SUBTITLE_NO_CHANGE

        string = cls.SUBTITLE_TEMPLATE.replace("%n", str(amount))

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

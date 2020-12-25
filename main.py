from PIL import Image
import os
from instabot import Bot as Instabot
from datetime import datetime

import logging
from logging.handlers import TimedRotatingFileHandler

from translator import Country, StringManager
from painter import ImageGenerator, SingleDataPoster, PosterText
from api import Covid19API, multipleDaysData


formatter = logging.Formatter("[%(asctime)s] (%(levelname)s) | %(message)s")

file_handler = TimedRotatingFileHandler(
    "main.log", when="midnight", backupCount=3)
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)


class NewCovidStatsInstagramBot:

    TEMPLATE_IMAGE_PATH = os.path.join('assets', 'background-template.png')
    STATS_OF_X_DAYS = 60

    SUBTITLES_COLOR = "#aaaaaa"
    ACCENT_COLOR = "#424242"

    def __init__(self, country_code: str,):
        self._country = Country(country_code)

        sm = StringManager()
        sm.config_country_translator(self._country)
        self._string_manager = sm

        self.__data = None
        self.__insta_username = os.environ.get("COVID_INSTAGRAM_USERNAME")
        self.__insta_password = os.environ.get("COVID_INSTAGRAM_PASSWORD")

    @property
    def instagram_username(self,):
        return self.__insta_username

    @property
    def instagram_password(self,):
        return self.__insta_password

    def get_data(self,) -> multipleDaysData:
        if self.__data is None:
            self.__data = Covid19API.get_stats(self._country.code)
        return self.__data

    def to_image(self,) -> Image.Image:
        """ Returns a Pillow Image instance that represents the covid
        status in the country. """

        data = self.get_data()

        yesterday_compare = data.compare_to_yesterday()
        today_r_value = data.last_day_r_value()

        img_gen = ImageGenerator(Image.open(self.TEMPLATE_IMAGE_PATH))
        img_gen.set_string_manager(self._string_manager)

        img_gen.add_background(today_r_value)
        img_gen.add_data(
            data=[
                SingleDataPoster(
                    self._string_manager.deaths,
                    now=yesterday_compare.new.deaths,
                    prev=yesterday_compare.old.deaths,
                ),
                SingleDataPoster(
                    self._string_manager.active_cases,
                    now=yesterday_compare.new.active_cases,
                    prev=yesterday_compare.old.active_cases,
                ),
                SingleDataPoster(
                    self._string_manager.recovered,
                    now=yesterday_compare.new.recovered_cases,
                    prev=yesterday_compare.old.recovered_cases,
                ),
            ],
            start_relative_y=0.07,
            end_relative_y=0.19,
        )

        img_gen.add_poster_title(
            PosterText([
                self._string_manager.new_cases,
                yesterday_compare.confirmed_diff_str(min_len=4),
            ]),
            y_relative=0.45,
            side="l",
            color=self.ACCENT_COLOR,
        )

        cases_data = data.get_cases_a_day_list()[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph(
            data=cases_data,
            r_value=today_r_value,
            relative_size=(0.475, 0.250),
            relative_pos=(0.7, 0.475),
            title=self._string_manager.new_cases_graph_title(
                days=len(cases_data)),
            title_color=self.SUBTITLES_COLOR,
            accent_color=self.ACCENT_COLOR,
        )

        img_gen.add_poster_title(
            PosterText([
                self._string_manager.basic_reproduction,
                f"{today_r_value:.2f}",
            ]),
            y_relative=0.75,
            side="r",
            color=self.ACCENT_COLOR,
        )

        r_value_data = data.get_r_values()[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph_r_values(
            data=r_value_data,
            r_value=today_r_value,
            guide_color=self.ACCENT_COLOR,
            relative_size=(0.475, 0.250),
            relative_pos=(0.3, 0.775),
            title=self._string_manager.r_graph_title(days=len(r_value_data)),
            title_color=self.SUBTITLES_COLOR,
            accent_color=self.ACCENT_COLOR,
        )

        subtitle_string = self._string_manager.subtitle(
            username=self.instagram_username)
        img_gen.add_subtitle(subtitle_string, color=self.SUBTITLES_COLOR)

        return img_gen.image

    def upload_image(self,
                     img_path: str,
                     caption: str = None,
                     ):
        """ Recives a path to an image, and uploads the given image to the
        Instagram account saved in the login info file.
        """

        if (not self.instagram_username) or (not self.instagram_password):
            raise ValueError(
                "Environment variables not found.\nPlease set the environment variables 'COVID_INSTAGRAM_USERNAME' and 'COVID_INSTAGRAM_PASSWORD'."
            )

        # Load the Instagram bot
        bot = Instabot()
        bot.login(username=self.instagram_username,
                  password=self.instagram_password)

        # upload the given photo
        bot.upload_photo(img_path, caption=caption, options={"rename": False})

    def genereate_and_upload(self,
                             temp_image_name: str = "tempimg.jpg",
                             ):
        """ Generate a new image, and upload it to Instagram. """

        # Generate and save the covid image.
        img = self.to_image().convert("RGB")
        img.save(temp_image_name)

        # Upload the image to instagram
        caption = self.get_caption()
        self.upload_image(temp_image_name, caption,)

        os.remove(temp_image_name)

    def upload_if_new_data(self,):

        logger.info("Checking for new information...")

        if Covid19API.get_changes().check_if_new(self._country.code):
            # If there is new data
            logger.info("New data found, generating and uploading image.")
            self.genereate_and_upload()

        else:
            # If there is no new data...
            logger.info("No new data found.")

    def get_caption(self,):
        country_code = self._country.code.upper()
        country_name = self._country.lang_locale.territories[country_code]
        return self._string_manager.caption(country=country_name)


if __name__ == "__main__":
    NewCovidStatsInstagramBot('il').upload_if_new_data()

from PIL import Image
import os
from instabot import Bot as Instabot
from datetime import datetime
import locale
import json

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


class CovidStatsInstagramBot:

    TEMPLATE_IMAGE_PATH = os.path.join('assets', 'background-template.png')
    STATS_OF_X_DAYS = 60

    SUBTITLES_COLOR = "#aaaaaa"
    ACCENT_COLOR = "#424242"

    def __init__(self,
                 country_code: str,
                 username: str = None,
                 string_manager: StringManager = None,
                 ):
        self._country = Country(country_code)

        if string_manager is None:
            string_manager = StringManager()
            string_manager.config_country_translator(self._country)
        self._sm = string_manager

        self.__data = None
        self.__insta_username = username

    @property
    def instagram_username(self,):
        return self.__insta_username

    def get_data(self,) -> multipleDaysData:
        if self.__data is None:
            self.__data = Covid19API.get_stats(self._country.code)
        return self.__data

    def to_image(self,
                 username: str = None,
                 ) -> Image.Image:
        """ Returns a Pillow Image instance that represents the covid
        status in the country. """

        if username is None:
            username = self.instagram_username

        data = self.get_data()

        yesterday_compare = data.compare_to_yesterday()
        today_r_value = data.last_day_r_value()

        img_gen = ImageGenerator(Image.open(self.TEMPLATE_IMAGE_PATH))
        img_gen.set_string_manager(self._sm)

        img_gen.add_background(today_r_value)
        img_gen.add_data(
            data=[
                SingleDataPoster(
                    self._sm.deaths,
                    now=yesterday_compare.new.deaths,
                    prev=yesterday_compare.old.deaths,
                ),
                SingleDataPoster(
                    self._sm.active_cases,
                    now=yesterday_compare.new.active_cases,
                    prev=yesterday_compare.old.active_cases,
                ),
                SingleDataPoster(
                    self._sm.recovered,
                    now=yesterday_compare.new.recovered_cases,
                    prev=yesterday_compare.old.recovered_cases,
                ),
            ],
            start_relative_y=0.07,
            end_relative_y=0.19,
        )

        img_gen.add_poster_title(
            PosterText([
                self._sm.new_cases,
                self._sm.format_number(
                    yesterday_compare.confirmed_diff, leading_zeros=4),
            ]),
            y_relative=0.425,
            side="l",
            color=self.ACCENT_COLOR,
        )

        cases_data = data.get_cases_a_day_list()[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph(
            data=cases_data,
            r_value=today_r_value,
            relative_size=(0.475, 0.250),
            relative_pos=(0.7, 0.45),
            title=self._sm.new_cases_graph_title(
                days=len(cases_data)),
            title_color=self.SUBTITLES_COLOR,
            accent_color=self.ACCENT_COLOR,
        )

        img_gen.add_poster_title(
            PosterText([
                self._sm.basic_reproduction,
                self._sm.format_number(today_r_value, floating_max=3),
            ]),
            y_relative=0.725,
            side="r",
            color=self.ACCENT_COLOR,
        )

        r_value_data = data.get_r_values()[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph_r_values(
            data=r_value_data,
            r_value=today_r_value,
            guide_color=self.ACCENT_COLOR,
            relative_size=(0.475, 0.250),
            relative_pos=(0.3, 0.75),
            title=self._sm.r_graph_title(days=len(r_value_data)),
            title_color=self.SUBTITLES_COLOR,
            accent_color=self.ACCENT_COLOR,
        )

        subtitle_string = self._sm.subtitle(username=username)
        img_gen.add_subtitle(subtitle_string, color=self.SUBTITLES_COLOR)

        return img_gen.image

    def upload_image(self,
                     img_path: str,
                     password: str,
                     username: str = None,
                     caption: str = None,
                     ):
        """ Recives a path to an image, and uploads the given image to the
        Instagram account saved in the login info file.
        """

        if username is None:
            username = self.instagram_username

        bot = Instabot()
        bot.login(username=username, password=password)
        bot.upload_photo(img_path, caption=caption,
                         options={"rename": False})

    def generate_and_upload(self,
                            password: str,
                            username: str = None,
                            temp_image_name: str = "tempimg.jpg",
                            ):
        """ Generate a new image, and upload it to Instagram. """

        if username is None:
            username = self.instagram_username

        # Generate and save the covid image.
        img = self.to_image(username=username).convert("RGB")
        img.save(temp_image_name)

        # Upload the image to instagram
        caption = self.get_caption()
        self.upload_image(img_path=temp_image_name, caption=caption,
                          username=username, password=password)

        os.remove(temp_image_name)

    def get_caption(self,):
        country_code = self._country.code.upper()
        country_name = self._country.lang_locale.territories[country_code]
        return self._sm.caption(country=country_name)


class ConfigFile:

    def __init__(self, path_to_file: str):
        with open(path_to_file, 'r', encoding='utf-8') as f:
            self.__content = json.load(f)

        self.__validate_content()
        self.__iter = iter(self.__content)

    def __validate_content(self,):
        assert isinstance(
            self.__content, dict), "Config file must be a json dictionary"

    def __iter__(self,):
        return self

    def __next__(self,):
        country_code = next(self.__iter)
        country = Country(country_code)
        data = self.__content[country_code]
        return CountryConfig(country, data)


class CountryConfig:

    def __init__(self, country: Country, data: dict):
        self.__country = country

        self.__validate_data(data)
        self.__data = data

    def __validate_data(self, data: dict):
        assert isinstance(data, dict), "Country data must be a dict"

        if "instagram" in data:
            instagram_data = data["instagram"]
            assert isinstance(
                instagram_data, dict), "Instagram data must be represented in a dictionary"

            assert "username" in instagram_data, "Instagram data must include username and password"
            assert "password" in instagram_data, "Instagram data must include username and password"

            assert isinstance(
                instagram_data["username"], str), "Instagram username must be a string"
            assert isinstance(
                instagram_data["password"], str), "Instagram password must be a string"

        if "translations" in data:
            translations_data = data["translations"]

            assert isinstance(
                translations_data, dict), "Translations must be represented in a dictionary"

            for translation in translations_data:
                assert isinstance(
                    translations_data[translation], str), "Translation must be a string"

    def to_string_manager(self,) -> StringManager:
        """ Returns a new instance of the `StringManager` object, that matches
        the settings from this country config file. """

        sm = StringManager()
        sm.config_country_translator(
            country=self.country,
            translations=self.translations
        )
        return sm

    def to_bot(self,) -> CovidStatsInstagramBot:
        return CovidStatsInstagramBot(
            country_code=self.country.code,
            username=self.instagram_login[0],
            string_manager=self.to_string_manager(),
        )

    @property
    def country(self,):
        return self.__country

    @property
    def instagram_login(self,):
        if "instagram" not in self.__data:
            return None, None

        instagram_data = self.__data["instagram"]
        return instagram_data["username"], instagram_data["password"]

    @property
    def translations(self,):
        if "translations" not in self.__data:
            return dict()

        return self.__data["translations"]


def main():
    logger.info("Checking for new information...")
    changes = Covid19API.get_changes()

    for country_config in ConfigFile('config.json'):
        country_code = country_config.country.code

        if changes.check_if_new(country_code):
            logger.info(f"{country_config.country.name} - New data found")

            username, password = country_config.instagram_login
            country_config.to_bot().generate_and_upload(
                username=username,
                password=password
            )

            logger.info(
                f"{country_config.country.name} - Uploaded image to @{username}")


if __name__ == "__main__":
    main()

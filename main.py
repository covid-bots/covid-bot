import os
import typing
import json

import logging
from logging.handlers import TimedRotatingFileHandler

from PIL import Image
from instabot import Bot as Instabot

from translator import Country, StringManager
from painter import ImageGenerator, SingleDataPoster, PosterText
from hopkins_api import CovidHistoryDatabase, CountryData


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

    __api = None

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

        self.__country_data_obj = None
        self.__insta_username = username

    def __get_api(self,) -> CovidHistoryDatabase:
        """ Returns the `CovidHistoryDatabase` instance used to generate
        the image. """

        if self.__api is None:
            self.__api = CovidHistoryDatabase()
        return self.__api

    def _get_country_data(self,) -> typing.Optional[CountryData]:
        """ Returns an instance that represents the covid stats in the current
        country. Returns `None` if data is not found. """

        if self.__country_data_obj is None:
            self.__country_data_obj = self.__get_api().country(self._country.name)

        return self.__country_data_obj

    @property
    def instagram_username(self,):
        return self.__insta_username

    def to_image(self,
                 username: str = None,
                 ) -> Image.Image:
        """ Returns a Pillow Image instance that represents the covid
        status in the country. """

        if username is None:
            username = self.instagram_username

        data = self._get_country_data()

        img_gen = ImageGenerator(Image.open(self.TEMPLATE_IMAGE_PATH))
        img_gen.set_string_manager(self._sm)

        img_gen.add_background(data.r_value)
        img_gen.add_data(
            data=[
                SingleDataPoster(
                    self._sm.deaths,
                    now=data.deaths,
                    prev=data.deaths_yesterday,
                ),
                SingleDataPoster(
                    self._sm.active_cases,
                    now=data.active,
                    prev=data.active_yesterday,
                ),
                SingleDataPoster(
                    self._sm.recovered,
                    now=data.recovered,
                    prev=data.recovered_yesterday,
                ),
            ],
            start_relative_y=0.07,
            end_relative_y=0.19,
        )

        img_gen.add_poster_title(
            PosterText([
                self._sm.new_cases,
                self._sm.format_number(
                    data.new_cases,
                    leading_zeros=4
                ),
            ]),
            y_relative=0.425,
            side="l",
            color=self.ACCENT_COLOR,
        )

        cases_data = data.new_cases_each_day[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph(
            data=cases_data,
            r_value=data.r_value,
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
                self._sm.format_number(data.r_value, floating_max=2),
            ]),
            y_relative=0.725,
            side="r",
            color=self.ACCENT_COLOR,
        )

        r_value_data = data.r_values_each_day[-self.STATS_OF_X_DAYS:]
        img_gen.add_graph_r_values(
            data=r_value_data,
            r_value=data.r_value,
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

    for country_config in ConfigFile('config.json'):

        username, password = country_config.instagram_login
        country_config.to_bot().generate_and_upload(
            username=username,
            password=password
        )

        logger.info(
            "%s - Uploaded image to @%s",
            country_config.country.name,
            username,
        )


if __name__ == "__main__":
    main()

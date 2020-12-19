import babel
import babel.languages
from bidi.algorithm import get_display
from googletrans import Translator

from typing import Union
import os
import json


class Country:

    def __init__(self, country_code: str):
        self._assert_valid_country_code(country_code)

        base_lang = babel.Locale('en')

        self.__code = country_code.upper()
        self.__name = base_lang.territories[self.code]
        self.__lang_code = self._get_territory_language_code(self.code).upper()
        self.__lang_locale = babel.Locale(self.lang_code.lower())
        self.__lang_name = self.lang_locale.get_display_name(base_lang)

    @property
    def code(self):
        return self.__code

    @property
    def name(self):
        return self.__name

    @property
    def lang_code(self):
        return self.__lang_code

    @property
    def lang_locale(self):
        return self.__lang_locale

    @property
    def lang_name(self):
        return self.__lang_name

    @staticmethod
    def _get_territory_language_code(code: str):
        info = babel.languages.get_territory_language_info(code)
        return max(info, key=lambda lang_code: info[lang_code]["population_percent"])

    @staticmethod
    def _assert_valid_country_code(code: str):
        """ Assert that the country code passed as a parameter is valid.
        Raises an Type/Value Errors if needed. """

        if not isinstance(code, str):
            raise TypeError("Country code must be a string")

        if len(code) != 2:
            raise ValueError("Country code must be a 2 character string")

    def __str__(self):
        string = str()
        return f"Country({self.name}, {self.code}), PopularLanguage({self.lang_name}, {self.lang_code})"


class StringManager:

    __BASE_LANG_CODE = "en"
    __LANG_FOLDER_PATH = "lang_config"
    __LANG_TRANSLATION_FILENAME_FORMAT = "{code}_translation.json"

    def __init__(self,):
        self.translator_delete()

    def config_translator(self, dest_lang: str) -> None:
        self.__check_valid_lang_code(dest_lang)
        self.__translator = Translator()
        self.__dest_lang = dest_lang.lower()
        self.__translations = dict()

        trans_filepath = os.path.join(
            self.__LANG_FOLDER_PATH, self.__dest_lang,
            self.__LANG_TRANSLATION_FILENAME_FORMAT.replace(
                '{code}', self.__dest_lang)
        )

        if os.path.exists(trans_filepath):
            with open(trans_filepath, encoding='utf-8') as f:
                self.__translations = json.load(f)

    def config_country_translator(self, country: Union[Country, str]) -> None:
        if not isinstance(country, Country):
            country = Country(country)

        self.config_translator(country.lang_code)

    @staticmethod
    def __check_valid_lang_code(code: str):
        if not isinstance(code, str):
            raise TypeError("Language code must be a string.")

        if len(code) != 2:
            raise ValueError("Language code must be two characters long.")

    def translator_delete(self,):
        """ Delete the configuration of the translator. """
        self.__translator = None
        self.__dest_lang = None
        self.__translations = dict()

    def from_translations(self, key: str):
        key = key.lower()

        if key in self.__translations:
            return self.__translations[key]

    def translate(self, string: str,) -> str:

        if self.__translator is None:
            return None

        if self.__dest_lang.lower() == self.__BASE_LANG_CODE.lower():
            return string

        return self.__translator.translate(
            string,
            dest=self.__dest_lang,
            src=self.__BASE_LANG_CODE,
        ).text

    def __get_property(self,
                       key: str,
                       base_str: str,
                       **replacing_dict,
                       ):

        file_translation = self.from_translations(key)
        if file_translation is not None:
            return self.__replace(file_translation, **replacing_dict)

        base_str = self.__replace(base_str, **replacing_dict)
        translation = self.translate(base_str)
        if translation is not None:
            return translation

        return base_str

    @classmethod
    def __replace(cls, string: str, **replacing_dict):

        if not replacing_dict:
            return string

        key = list(replacing_dict.keys())[0]
        string = string.replace(f"{{{key}}}", str(replacing_dict[key]))
        del replacing_dict[key]

        return cls.__replace(string, **replacing_dict)

    @property
    def unchanged(self,) -> str:
        return self.__get_property("unchanged", "Unchanged")

    @property
    def unavailable(self,) -> str:
        return self.__get_property("unavailable", "Unavailable")

    @property
    def deaths(self,) -> str:
        return self.__get_property("deaths", "Deaths")

    @property
    def recovered(self,) -> str:
        return self.__get_property("recovered", "Recovered")

    @property
    def active_cases(self,) -> str:
        return self.__get_property("active_cases", "Active Cases")

    @property
    def new_cases(self,) -> str:
        return self.__get_property("new_cases", "New Cases")

    @property
    def basic_reproduction(self,) -> str:
        return self.__get_property("basic_reproduction", "Basic Reproduction (R)")

    def r_graph_title(self, days: int):
        return self.__get_property("r_graph_title",
                                   "Basic reproduction (R) in the last {days} days",
                                   days=days)

    def new_cases_graph_title(self, days: int):
        return self.__get_property("new_cases_graph_title",
                                   "New cases a day in the last {days} days",
                                   days=days)

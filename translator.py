import babel
import babel.languages
from bidi.algorithm import get_display
from googletrans import Translator
from typing import Union


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

    def __init__(self,):
        self.translator_delete()

    def config_translator(self, dest_lang: str) -> None:
        self.__check_valid_lang_code(dest_lang)
        self.__translator = Translator()
        self.__dest_lang = dest_lang

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

    def translate(self, string: str,) -> str:
        if self.__translator is None:
            raise PermissionError(
                "To translate strings, you must configure the translator using the `confign_translator` method.")

        return self.__translator.translate(
            string,
            dest=self.__dest_lang,
            src=self.__BASE_LANG_CODE
        ).text

    def convert(self, string: str) -> str:
        if (self.__translator is not None and
                self.__dest_lang != self.__BASE_LANG_CODE):
            string = self.translate(string)

        return get_display(string)

    def delta_str(self, num: int) -> str:
        if num == 0:
            return self.unchanged
        elif num > 0:
            return f"+{num}"
        else:
            return str(num)  # automatically adds the `-` sign

    @property
    def unchanged(self,) -> str:
        return self.convert("Unchanged")

    @property
    def unavailable(self,) -> str:
        return self.convert("Unavailable")

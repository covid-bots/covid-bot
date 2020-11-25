from purl import URL
import requests

from exceptions import *


class API:

    MAIN_URL = URL("https://api.covid19api.com")

    def __request(url: URL) -> requests.Response:
        """ Make an http request, and check for errors. """

        response = requests.get(url=url.as_string())

        # Check if data loaded correctly
        if response.status_code != 200:
            raise requestAPIError(
                f"{url}:\nResponse status {response.status_code}.")

        return response.json()

    @classmethod
    def __create_path_from_segments(cls, *args) -> URL:
        """ Returns an url object, representing the main url with the given path
        segments.

        For example, if the main url is `google.com`, and the arguments
        passed are `foo` and `bar`, the returned url will represent
        `google.com/foo/bar`.
        """

        url = cls.MAIN_URL

        for arg in args:
            url = url.add_path_segment(arg)

        return url

    @classmethod
    def get_day_one_all_stats(cls, country: str, last_x_days: int = None):
        """ Returns all cases by case type for a country from the first recorded
        case. """

        # Make a request to the api
        request_url = cls.__create_path_from_segments(
            "dayone", "country", country)
        response_json = cls.__request(request_url)

        if last_x_days:
            response_json = response_json[-last_x_days:]

        return [SingleDayData(day_data_dict)
                for day_data_dict in response_json]


class SingleDayData:
    """ Represents Covid data about a single day, from a single country. """

    __raw_data_dict = None
    __VALID_DICT_KEYS = {"Country", "CountryCode", "Province", "City", "CityCode",
                         "Lat", "Lon", "Confirmed", "Deaths", "Recovered", "Active", "Date"}

    def __init__(self, data_dict: dict):

        self.__check_valid_data(data_dict)
        self.__raw_data_dict = data_dict

    @classmethod
    def __check_valid_data(cls, data_dict: dict):
        """ Checks if the given dict is a valid data dict.
        If not, raises an error. """

        if len(data_dict) != len(cls.__VALID_DICT_KEYS):
            cls.__raise_data_error()

        if set(data_dict.keys()) != cls.__VALID_DICT_KEYS:
            cls.__raise_data_error()

    @staticmethod
    def __raise_data_error():
        raise ValueError("The given data dict is not a valid one.")

    @property
    def confirmed_cases(self):
        return self.__raw_data_dict["Confirmed"]

    @property
    def deaths(self):
        return self.__raw_data_dict["Deaths"]

    @property
    def recovered_cases(self):
        return self.__raw_data_dict["Recovered"]

    @property
    def active_cases(self):
        return self.__raw_data_dict["Active"]

    @property
    def date(self):
        return self.__raw_data_dict["Date"]


day = API.get_day_one_all_stats("Israelk", 1)
print(day[0].active_cases)

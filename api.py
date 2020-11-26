from exceptions import *
import pylab
import matplotlib.pyplot as plt
from purl import URL
import requests
import matplotlib as mpl


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


class multipleDaysData:

    def __init__(self, json_info):
        self.__raw = json_info
        self.__daydata = [SingleDayData(data) for data in json_info]
        self.__daydelta = [
            DayDataDiff(
                self.__daydata[index],
                self.__daydata[index-1]
            )
            for index in range(1, len(self.__daydata))
        ]

    def get_data_before_x_days(self, days: int):
        return SingleDayData(self.__raw[-days])

    def get_today(self,):
        return self.get_data_before_x_days(1)

    def get_yesterday(self,):
        return self.get_data_before_x_days(2)

    def get_deaths_list(self,):
        return [daydata.deaths for daydata in self.__daydata]

    def get_recovered_list(self,):
        return [daydata.recovered_cases for daydata in self.__daydata]

    def get_active_cases_list(self,):
        return [daydata.active_cases for daydata in self.__daydata]

    def get_cases_a_day_list(self,):
        return [daydelta.confirmed_diff for daydelta in self.__daydelta]


class DayDataDiff:

    """ Compare two `SingleDayData` objects. """

    def __init__(self, newest: SingleDayData, older: SingleDayData):
        self.__newest = newest
        self.__older = older

    @property
    def new(self):
        return self.__newest

    @property
    def old(self):
        return self.__older

    @staticmethod
    def __genrate_diff(newest_data, older_data):
        return newest_data - older_data

    @staticmethod
    def __generate_percentage_diff(newest_data, older_data):
        return (newest_data / older_data - 1) * 100

    @property
    def confirmed_diff(self):
        return self.__genrate_diff(self.__newest.confirmed_cases, self.__older.confirmed_cases)

    @property
    def confirmed_percentage_diff(self):
        return self.__generate_percentage_diff(self.__newest.confirmed_cases, self.__older.confirmed_cases)

    @property
    def deaths_diff(self):
        return self.__genrate_diff(self.__newest.deaths, self.__older.deaths)

    @property
    def deaths_percentage_diff(self):
        return self.__generate_percentage_diff(self.__newest.deaths, self.__older.deaths)

    @property
    def recovered_diff(self):
        return self.__genrate_diff(self.__newest.recovered_cases, self.__older.recovered_cases)

    @property
    def recovered_percentage_diff(self):
        return self.__generate_percentage_diff(self.__newest.recovered_cases, self.__older.recovered_cases)

    @property
    def active_diff(self):
        return self.__genrate_diff(self.__newest.active_cases, self.__older.active_cases)

    @property
    def active_percentage_diff(self):
        return self.__generate_percentage_diff(self.__newest.active_cases, self.__older.active_cases)


class Covid19API:

    MAIN_URL = URL("https://api.covid19api.com")

    def __request(url: URL) -> list:
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
    def get_stats(cls, country: str, last_x_days: int = None):
        """ Returns all cases by case type for a country from the first recorded
        case. """

        # Make a request to the api
        request_url = cls.__create_path_from_segments(
            "dayone", "country", country)
        response_json = cls.__request(request_url)

        if last_x_days:
            response_json = response_json[-last_x_days:]

        return multipleDaysData(response_json)

    @classmethod
    def get_today_stats(cls, country: str):
        """ Returns the data Covid data TODAY from the given country. """
        return cls.get_stats(country, last_x_days=1)[0]

    @staticmethod
    def compare_day_data(newest: SingleDayData, older: SingleDayData) -> DayDataDiff:
        """ Compares the two day data objects, and returns an `DayDataDiff`
        instance. """
        return DayDataDiff(newest=newest, older=older)

    @classmethod
    def compare_last_two_days(cls, country: str):
        """ Compares the data from today and yesterday,
        and returns an `DayDataDiff` object. """

        data = cls.get_stats(country, last_x_days=2)
        return cls.compare_day_data(data.get_today(), data.get_yesterday())

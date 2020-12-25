from exceptions import *

from purl import URL
import requests

from typing import List, Dict, Set
import logging


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

        raw = self.__normalize_data(json_info)
        self.__raw = self.__modify_to_monotonically_increasing(
            raw, properties_to_modify={"Recovered", "Confirmed", "Deaths"}
        )

        self.__daydata = [SingleDayData(data) for data in self.__raw]
        self.__daydelta = [
            DayDataDiff(
                self.__daydata[index],
                self.__daydata[index-1]
            )
            for index in range(1, len(self.__daydata))
        ]

    @staticmethod
    def __normalize_data(json_info: list):
        """ Some countries have more then one province. This method will remove
        the data from the different province, and will only keep the main data.
        """

        discovered_dates = set()
        normal_data = list()

        for data in json_info:

            if data["Date"] in discovered_dates:

                # Pull the saved data
                # & remove the pulled data from the list

                for index, element in enumerate(normal_data):
                    if element["Date"] == data["Date"]:
                        saved_data = normal_data.pop(index)
                        break

                new_data = dict()
                for key in saved_data:

                    if isinstance(data[key], float) or isinstance(data[key], int):
                        new_data[key] = saved_data[key] + data[key]

                    if isinstance(data[key], str):
                        if data[key] in saved_data[key]:
                            new_data[key] = saved_data[key]
                        else:
                            new_data[key] = f"{saved_data[key]}, {data[key]}"

                    else:
                        new_data[key] = saved_data[key]

                normal_data.append(new_data)
            else:
                discovered_dates.add(data["Date"])
                normal_data.append(data)

        return normal_data

    @staticmethod
    def __modify_to_monotonically_increasing(data: List[Dict],
                                             properties_to_modify: Set[str]
                                             ) -> List[Dict]:

        modified_count = 0
        modified_max = len(properties_to_modify) * len(data)

        new_data = list(data[0])
        for prev_i in range(len(data) - 1):
            cur_i = prev_i + 1

            assert data[cur_i].keys() == data[prev_i].keys()
            for key in data[cur_i]:
                if key in properties_to_modify:
                    if data[prev_i][key] > data[cur_i][key]:
                        data[cur_i][key] = data[prev_i][key]
                        modified_count += 1

        if modified_count > 0:
            logging.warning(
                f"API: Modified {modified_count} values out of {modified_max} in total ({round(modified_count/modified_max*100, 2)}%)")

        return data

    def get_data_before_x_days(self, days: int):
        return self.__daydata[-days]

    def get_today(self,):
        return self.get_data_before_x_days(1)

    def get_yesterday(self,):
        return self.get_data_before_x_days(2)

    def compare_dates(self, date1: int, date2: int):
        new = self.get_data_before_x_days(min(date1, date2))
        old = self.get_data_before_x_days(max(date1, date2))
        return DayDataDiff(new, old)

    def compare_to_yesterday(self):
        """ Returns a `DayDataDiff` object that represents the data changes
        accrued between today and yesterday. """
        return self.compare_dates(1, 2)

    def get_deaths_list(self,):
        return [daydata.deaths for daydata in self.__daydata]

    def get_recovered_list(self,):
        return [daydata.recovered_cases for daydata in self.__daydata]

    def get_active_cases_list(self,):
        return [daydata.active_cases for daydata in self.__daydata]

    def get_day_delta(self, day_jumps: int = 1):
        """ Returns a list of `DayDataDiff` object. Each instance
        compares to the day `day_jumps` days before. For example, if `day_jumps=1`,
        the returned list will represent the differences between each day. If
        `day_jumps=7`, each instance will represent the different between this day
        and the day 7 days before it. """

        return [
            DayDataDiff(
                self.__daydata[index],
                self.__daydata[index-day_jumps]
            )
            for index in range(day_jumps, len(self.__daydata))
        ]

    def get_x_cases_a_day_average_list(self, last_x_days: int,):
        return [delta.confirmed_diff/last_x_days
                for delta in self.get_day_delta(last_x_days)]

    def get_cases_a_day_list(self,):
        return [daydelta.confirmed_diff for daydelta in self.get_day_delta()]

    def get_r_values(self,):
        """ Calculated using the formula described in:
        https://www.ynet.co.il/health/article/Bk5KKJOYv
        """

        week_averages = self.get_x_cases_a_day_average_list(7)
        days = len(week_averages) - 7
        r_list = list()

        for cur_index in range(days):
            cur_week = week_averages[cur_index + 7]
            prev_week = week_averages[cur_index]

            if cur_week == 0:
                cur_r_value = 0

            if prev_week == 0:
                cur_r_value = 1
            else:
                cur_r_value = (cur_week / prev_week) ** (4/7)

            r_list.append(cur_r_value)

        return r_list

    def last_day_r_value(self,):
        return self.get_r_values()[-1]


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

    def confirmed_diff_str(self, min_len: int = 0):
        diff = str(self.confirmed_diff)
        zeros_to_add = max([min_len - len(diff), 0])
        zeros = "0" * zeros_to_add
        return zeros + diff

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

    @staticmethod
    def __request(url: URL) -> list:
        """ Make an http request, and check for errors. """

        response = requests.get(url=url.as_string(), verify=False)

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
    def get_stats(cls, country: str):
        """ Returns all cases by case type for a country from the first recorded
        case. """

        # Make a request to the api
        request_url = cls.__create_path_from_segments(
            "total", "dayone", "country", country)
        response_json = cls.__request(request_url)

        return multipleDaysData(response_json)

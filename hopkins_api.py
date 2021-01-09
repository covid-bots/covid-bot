""" In the past, this project was based on the API provided by https://covid19api.com.
However, we found out that this API was unreliable, and provided not accurate data.
This file contains the new API implementation, which is provided by the JHU CSSE.
You can find more information about the API at https://github.com/CSSEGISandData/COVID-19
"""

import typing
import datetime
import logging
import csv
import requests


class CountryData:
    """ An object that stores a collection of Covid19 data of
    a specific country. """

    def __init__(self,
                 data: typing.List[dict],
                 ):
        """ Constructed by the `CovidHistoryDatabase` object, and should not be
        initialized by the user. Recives a data dict, and stores it. """
        self.__data = data

    @property
    def data(self,) -> typing.List[dict]:
        """ Returns the raw data that is saved in the instance. """
        return self.__data

    @property
    def confirmed_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the total confirmed
        cases discovered up to the date that the cell represents. The first
        cell represents the 22nd of January 2020, and the last cell represent
        the newest data (today / yesterday). """

        return [data['confirmed'] for data in self.data]

    @property
    def confirmed(self,) -> int:
        """ The total confirmed Covid19 cases up to date. """
        return self.confirmed_each_day[-1]

    @property
    def confirmed_yesterday(self,) -> int:
        """ The total confirmed Covid19 cases, up until yesterday. """
        return self.confirmed_each_day[-2]

    @property
    def deaths_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the total death
        cases discovered up to the date that the cell represents. The first
        cell represents the 22nd of January 2020, and the last cell represent
        the newest data (today / yesterday). """

        return [data['deaths'] for data in self.data]

    @property
    def deaths(self, ) -> int:
        """ The total death cases due to Covid19 up to date. """
        return self.deaths_each_day[-1]

    @property
    def deaths_yesterday(self,) -> int:
        """ The total death cases due to Covid19 up until yesterday. """
        return self.deaths_each_day[-2]

    @property
    def deaths_diff_today(self,) -> int:
        """ The amount of new death cases recorded between today and yesterday. """
        return self.deaths_each_day[-1] - self.deaths_each_day[-2]

    @property
    def recovered_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the total recovered
        cases discovered up to the date that the cell represents. The first
        cell represents the 22nd of January 2020, and the last cell represent
        the newest data (today / yesterday). """

        return [data['recovered'] for data in self.data]

    @property
    def recovered(self,) -> int:
        """ The total recorded recovered Covid19 cases up to date. """
        return self.recovered_each_day[-1]

    @property
    def recovered_yesterday(self,) -> int:
        """ The total recorded recovered Covid19 cases up until to yesterday. """
        return self.recovered_each_day[-2]

    @property
    def recovered_diff_today(self,) -> int:
        """ The delta (difference) in recovered cases between today and yesterday. """
        return self.recovered_each_day[-1] - self.recovered_each_day[-2]

    @property
    def active_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the amount of
        active cases in the date that the cell represents. The first
        cell represents the 22nd of January 2020, and the last cell
        represent the newest data (today / yesterday). """
        return [
            confirmed - recovered - deaths
            for confirmed, recovered, deaths
            in zip(self.confirmed_each_day, self.recovered_each_day, self.deaths_each_day)
        ]

    @property
    def active(self,) -> int:
        """ The amount of active cases in the newest data (today / yesterday)."""
        return self.active_each_day[-1]

    @property
    def active_yesterday(self,) -> int:
        """ The amount of active cases in the represented country, yesterday. """
        return self.active_each_day[-2]

    @property
    def active_diff_today(self,) -> int:
        """ The delta (difference) in active cases between today and yesterday. """
        return self.active_each_day[-1] - self.active_each_day[-2]

    @property
    def new_cases_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the number of
        cases discovered each day. The first cell represents the 22nd of January
        2020, and the last cell represent the newest data (today / yesterday)
        """

        total = self.confirmed_each_day
        new = list()

        for index in range(1, len(total)):
            new.append(total[index] - total[index-1])

        return new

    @property
    def new_cases(self,) -> int:
        """ The number of cases that were discovered in the last day. """
        return self.new_cases_each_day[-1]

    @property
    def new_cases_yesterday(self,) -> int:
        """ The amount of new cases recorded yesterday. """
        return self.new_cases_each_day[-2]

    def __new_cases_x_days_averages(self, days: int) -> typing.List[float]:
        """ Same as `new_cases_each_day`, but instead of representing each
        day with its own new cases, it is represented as a average of the
        new cases in the last `days` days. This results in a much more 'smooth
        curve', instead of a graph with hard spikes. Used to calculate the
        R values, for example. """

        new_cases = self.new_cases_each_day
        averages = list()

        for index in range(days - 1, len(new_cases)):
            total_cases = sum(
                new_cases[index - day]
                for day in range(days)
            )

            averages.append(total_cases / days)

        return averages

    @property
    def new_cases_weekly_averages(self,) -> typing.List[float]:
        """ A list of floating numbers, where each cell represents the average
        number of new cases discovered each day, in the past week.
        The first cell represents the week between the 22nd of January 2020,
        and the 29th, the second cell represents the week 23-30, etc.
        The last cell represents the newest data - average new cases in the
        last week. """
        return self.__new_cases_x_days_averages(7)

    @property
    def r_values_each_day(self,) -> typing.List[float]:
        """ A list of floating numbers, where each cell represents the R value
        each day. The first cell represents the 22nd of January 2020, and the
        last cell represent the newest data (today / yesterday). Calculated
        using the formula described in https://ynet.co.il/health/article/Bk5KKJOYv
        """

        weekly_averages = self.new_cases_weekly_averages
        r_list = list()

        for cur_index in range(7, len(weekly_averages)):
            cur_week = weekly_averages[cur_index]
            prev_week = weekly_averages[cur_index - 7]

            if cur_week == 0:
                cur_r_value = 0.0

            elif prev_week == 0:
                cur_r_value = 1.0

            else:
                cur_r_value = (cur_week / prev_week) ** (4/7)

                if isinstance(cur_r_value, complex):
                    cur_r_value = 0.0

            r_list.append(cur_r_value)

        return r_list

    @property
    def r_value(self,) -> float:
        """ The most recent R value. Calculated using the formula
        described in https://ynet.co.il/health/article/Bk5KKJOYv """
        return self.r_values_each_day[-1]

    @property
    def r_value_yesterday(self,) -> float:
        """ The R value that represents the data from yesterday. """
        return self.r_values_each_day[-2]


class ApiFromCsv:
    """ Represents an API endpoint that contains data represented by a 
    csv table. Has a couple of methods that downloads and manipulates the
    data. """

    def __init__(self, url: str):
        """ When initialized, requests data from the API, downloads the csv sheet
        and saves it in memory. """

        self.__API_URL = url

        # Download and save the confirmend cases history
        sheet = self.__request()

        # Saves the first row as the `headers` row, and the other rows
        # as `content`.
        self._headers = sheet[0]
        self._content = self.__change_types(sheet[1:])

    @property
    def API_URL(self,):
        """ The source of the data - The API data url. """
        return self.__API_URL

    def __request(self,) -> typing.List[typing.List[str]]:
        """ Tries to download the csv sheet from the provided URL.
        Returns the data as a list of lists, where each element is a string.
        """

        logging.info("Downloading data...")

        response = requests.get(self.API_URL)
        self.__raw_response_content = response.content

        # Check if data loaded correctly
        if response.status_code != 200:
            raise RequestAPIError(
                f"{self.API_URL}:\nResponse status {response.status_code}.")

        # convert downloaded content (in binary) to a 2d list with rows and
        # columns not very efficient, saves the whole downloaded spreadsheet
        # in memory until the object is deleted.... it is what it is (:

        decoded_content = response.content.decode('utf8').splitlines()
        sheet_content = list(csv.reader(decoded_content))

        return sheet_content

    def __change_types(self,
                       content: typing.List[typing.List[str]]
                       ) -> typing.List[typing.Union[str, int, float, None]]:
        """ By default, data is provided in a list of strings. This methods
        recives one row of data, and for each element in the row, converts
        it into an integer or a float. """

        return [
            [
                self.__change_item_type(item)
                for item in row
            ]
            for row in content
        ]

    @staticmethod
    def __change_item_type(item: str) -> typing.Any:
        """ Convert the given string into an integer, float, leaves it a string,
        or even to `None` if the string is empty. """

        # try converting to integer.
        # if not possible, try converting to float
        # if not possible, try converting to string
        # if not possible (or empty string), returns `None`

        try:
            return int(item)

        except ValueError:

            try:
                return float(item)

            except ValueError:

                if str(item):
                    return str(item)

    @staticmethod
    def _content_to_list_of_dicts(content: typing.List[typing.List[typing.Any]],
                                  headers: typing.List[str],
                                  ) -> typing.List[typing.Dict[str, typing.Any]]:
        """ Converts the 2d list database content into a list of dictionaries.
        Each new dictionary in the list represent one row of content. """

        return [
            {
                header: data
                for header, data in zip(headers, row)
            }
            for row in content
        ]

    def save_csv(self, path: str):
        """ Saves the data into a spreadsheet in the given file path, as downloaded
        from the API (not including the modifications of the script). """

        with open(path, 'wb') as file:
            file.write(self.__raw_response_content)


class DateHistoryCvsApi(ApiFromCsv):
    """ Represents one Covid19 history endpoint. It can load and
    download the information from the endpoint url, manipulate
    and even save it. """

    def __init__(self,
                 url: str,
                 id_index: int = 0,
                 ):
        # Calling the super constructor will download the data
        # and save it in the `_content` and `_header` properties.
        # Usually the data is large (a couple of MB), and will
        # take a couple of seconds to download.
        super().__init__(url)

        logging.info("Prossecing the downloaded information...")

        # Converting the raw downloaded data and storing it
        # inside of a list of dictionaries
        date_data = self.__generate_date_data(id_index)
        self.__date_data = self.__squash_data_by_id(date_data)

    def __generate_date_data(self, id_index: int,):
        """ Converts the 'raw' downloaded data into a list of dictionaries.
        `id_index` is the index of the column that will be used to generate
        the `id` value for each dictionary. """

        dates, not_date_indexes = self.__generate_dates()

        return [
            {
                'id': row_data[id_index],
                'data': self.__generate_row_data(
                    row_data,
                    dates,
                    not_date_indexes,
                ),
            }

            for row_data in self._content
        ]

    def __generate_row_data(self,
                            row_data: list,
                            dates: list,
                            not_date_indexes: list,
                            ):
        """ Recives three lists:
        1. `row_data`: A list of the actual data from the current row.
        2. `dates`: A list of all of the valid dates from the downloaded data.
        3. `not_date_indexes`: A list of indexes in the `row_data` list, in which
            the value is not represented by a specific date from the `dates` list.

        This method will iterate over the list of dates and the row data, and will
        match each data item to a specific date, and will return a list of
        dictionaries, where in each dictionary the 'date' will contain the date,
        and the 'value' will contain the value from the `row_data` that matches
        the date. """

        dates = iter(dates)
        data = list()

        for index, value in enumerate(row_data):
            if index not in not_date_indexes:
                data.append({
                    'value': value,
                    'date': next(dates),
                })

        return data

    def __squash_data_by_id(self, data: typing.List[dict]):
        """ Recives a list of dictionaries that contain two keys - `id` and
        `data`. Iterates over teh list, and and merges the data of dictionaries
        that share the same `id`. """

        visited_ids = set()
        new_data = list()

        for cur_data in data:
            if cur_data['id'] in visited_ids:
                # if current id already visited -> needs to be merged!

                # finds the already visited object
                already_visited_index = next(
                    new_data.index(cur_visited)
                    for cur_visited in new_data
                    if cur_visited['id'] == cur_data['id']
                )

                # updates the current data with the merged data
                cur_data['data'] = self.__merge_same_ids(
                    cur_data,
                    data[already_visited_index],
                )

                # removes the already saves data from the visited list
                new_data.pop(already_visited_index)

            else:
                # if id not visited yet
                # gets added to the visited list!
                visited_ids.add(cur_data['id'])

            new_data.append(cur_data)

        return new_data

    def __merge_same_ids(self, data_one, data_two,):
        """ Recives two data objects (a list of dictionaties). Each dictionary
        has a `date` field that contains a `datetime.date` instance. This
        methods iterates over both lists, and creates a new list in which the
        data from both lists are merged into one list. """

        # generates the list of dates for each dataset
        one_dates = [cur['date'] for cur in data_one['data']]
        two_dates = [cur['date'] for cur in data_two['data']]

        # union date lists, maintain order
        dates = list(dict.fromkeys(one_dates + two_dates))

        new_data = list()

        # loop over the list of combined dates
        for date in dates:

            value = 0

            # tries to find data from first list that matches the
            # current date.
            try:
                value += next(
                    cur_data['value']
                    for cur_data in data_one['data']
                    if cur_data['date'] == date
                )

            except StopIteration:
                # if current date doesn't appear in any of the values in
                # the first list
                pass

            # tries to find data from the second that matches the
            # current date.
            try:
                value += next(
                    cur_data['value']
                    for cur_data in data_two['data']
                    if cur_data['date'] == date
                )

            except StopIteration:
                # if current date doesn't appear in any of the values in
                # the second list
                pass

            # adds the new combined data the the `new_data` list
            new_data.append({
                'date': date,
                'value': value,
            })

        return new_data

    def __generate_dates(self,) -> typing.Tuple[typing.List[datetime.date], typing.List[int]]:
        """ Generates a list of `datetime.date` instances from the list
        of data headers (the `self._header` property). In addition, returns
        a list of indexes that represents the headers that are NOT dates. """

        not_date_indexes = set()
        dates = list()

        for index, header in enumerate(self._headers):
            date = self.__string_to_date(header)

            if date is not None:
                dates.append(date)

            else:
                not_date_indexes.add(index)

        return dates, not_date_indexes

    @staticmethod
    def __string_to_date(date_string: str) -> datetime.date:
        """ Converts the date string recvied by the API into a `datetime.date`
        instance, and returns it. If can't convert the given string into
        a `date` instance, returns `None`. """

        try:
            month, day, year = date_string.split('/')
            month, day, year = (int(value) for value in (month, day, year))

            # API provides years with only 2 less significant digits.
            # For example, if the year is `2021`, the api will return only `21`.
            # This adds the `2000` part (:
            today = datetime.date.today()
            century = int(today.year / 100)
            year += century * 100

            return datetime.date(day=day, month=month, year=year,)

        except Exception:  # pylint: disable=broad-except
            # If can't convert given string to date, returns `None`
            return None

    def all_data(self,) -> typing.List[dict]:
        """ The raw total data. """
        return self.__date_data

    def data_by_id(self, data_id: str) -> list:
        """ Returns only the data by the given id. Use the `all_data` method
        to get a list of all id's. """

        try:
            return next(
                data['data']
                for data in self.all_data()
                if data['id'] == data_id
            )

        except StopIteration:
            raise TypeError(f"Invalid id {data_id}")

    def data_by_date(self, date: datetime.date) -> typing.List[dict]:
        """ Returns a list of dictionaries that only contain data from
        the given date. """

        data_list = list()

        for id_data in self.all_data():
            for date_data in id_data['data']:
                if date_data['date'] == date:
                    data_list.append({
                        'id': id_data['id'],
                        'value': date_data['value'],
                    })

        return data_list


# pylint: disable=line-too-long
# Source: JHU CSSE COVID-19 Data
# https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series
COVID_DEATHS_GLOBAL_HISTORY_ENDPOINT = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
COVID_CONFIRMED_GLOBAL_HISTORY_ENDPOINT = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
COVID_RECOVERED_GLOBAL_HISTORY_ENDPOINT = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv'


class CovidDeathsHistory(DateHistoryCvsApi):

    def __init__(self,):
        logging.info("Generating Covid 'deaths' history information...")

        super().__init__(
            url=COVID_DEATHS_GLOBAL_HISTORY_ENDPOINT,
            id_index=1,
        )


class CovidConfirmedHistory(DateHistoryCvsApi):

    def __init__(self,):
        logging.info("Generating Covid 'confirmed' history information...")

        super().__init__(
            url=COVID_CONFIRMED_GLOBAL_HISTORY_ENDPOINT,
            id_index=1,
        )


class CovidRecoveredHistory(DateHistoryCvsApi):

    def __init__(self,):
        logging.info("Generating Covid 'recovered' history information...")

        super().__init__(
            url=COVID_RECOVERED_GLOBAL_HISTORY_ENDPOINT,
            id_index=1,
        )


class CovidHistoryDatabase:

    def __init__(self,):

        self.__data = self.__combine_data({
            "confirmed": CovidConfirmedHistory().all_data(),
            "deaths": CovidDeathsHistory().all_data(),
            "recovered": CovidRecoveredHistory().all_data(),
        })

    def __combine_data(self, data: dict):

        types = list(data.keys())
        countries = list()

        for datasets in zip(*data.values()):

            country_dates = list()
            for date_sets in zip(*(dataset['data'] for dataset in datasets)):

                cur_data = {'date': date_sets[0]['date']}
                for date_data, cur_type in zip(date_sets, types):
                    cur_data[cur_type] = date_data['value']

                country_dates.append(cur_data)

            countries.append({
                'country': datasets[0]['id'],
                'data': country_dates,
            })

        return countries

    def countries(self,) -> typing.List[str]:
        """ Returns a list that has all of the names of the countries that are
        provided by the API. """

        return [data['country'] for data in self.all_data()]

    def all_data(self,):
        return self.__data

    def country_data(self, country: str):
        return next(
            data['data']
            for data in self.all_data()
            if data['country'] == country
        )

    def country(self, country: str):
        return CountryData(data=self.country_data(country))

    def date_data(self, date: datetime.date):

        data_list = list()

        for country_data in self.all_data():
            for date_data in country_data['data']:
                if date_data['date'] == date:

                    del date_data['date']
                    date_data['country'] = country_data['country']
                    data_list.append(date_data)

        return data_list


# - - E X C E P T I O N S - - #

class APIError(Exception):
    """ Raised when there is some sort of error while using the API """


class RequestAPIError(APIError):
    """ Raised when trying to pull data from the online API,
    but recives an error (Error code != 200) """

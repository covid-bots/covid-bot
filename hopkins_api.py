""" In the past, this project was based on the API provided by https://covid19api.com.
However, we found out that this API was unreliable, and provided not accurate data.
This file contains the new API implementation, which is provided by the JHU CSSE.
You can find more information about the API at https://github.com/CSSEGISandData/COVID-19
"""

import typing
from purl import URL
import requests
import csv


class CountryAPI:

    def __init__(self,
                 name: str,
                 province: typing.Optional[str],
                 lat: typing.Optional[float],
                 long: typing.Optional[float],
                 confirmed_each_day: typing.List[int],
                 ):
        self.__name = name
        self.__province = province
        self.__lat = lat
        self.__long = long
        self.__confirmed_each_day = confirmed_each_day

    @property
    def name(self,) -> str:
        """ The country name, as a string. """
        return self.__name

    @property
    def province(self,) -> typing.Optional[str]:
        """ The province or state, as a string.
        In some cases, will return `None`. """
        return self.__province

    @property
    def lat(self,) -> typing.Optional[float]:
        """ The latitude of the country, as a float.
        In some cases, will return `None`.
        NOTE: this can be inaccurate in a country with multiple states
        or provinces. For more information, check the `__merge_rows` method
        in the `Covid19API` object. """
        return self.__lat

    @property
    def long(self,) -> typing.Optional[float]:
        """ The longitude  of the country, as a float.
        In some cases, will return `None`.
        NOTE: this can be inaccurate in a country with multiple states
        or provinces. For more information, check the `__merge_rows` method
        in the `Covid19API` object. """
        return self.__long

    @property
    def confirmed_each_day(self,) -> typing.List[int]:
        """ A list of integers, where each cell represents the total confirmed
        cases discovered up to the date that the cell represents. The first
        cell represents the 22nd of January 2020, and the last cell represent
        the newest data (today / yesterday). """
        return self.__confirmed_each_day

    @property
    def total_confirmed_cases(self,) -> int:
        """ The total number of Covid cases discovered in the country. """
        return self.confirmed_each_day[-1]

    @property
    def new_cases(self,) -> int:
        """ The number of cases that were discovered in the last day. """
        return self.confirmed_each_day[-1] - self.confirmed_each_day[-2]

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
                cur_r_value = 0

            elif prev_week == 0:
                cur_r_value = 1

            else:
                cur_r_value = (cur_week / prev_week) ** (4/7)

            r_list.append(cur_r_value)

        return r_list

    @property
    def r_value(self,) -> float:
        """ The most recent R value. Calculated using the formula
        described in https://ynet.co.il/health/article/Bk5KKJOYv """
        return self.r_values_each_day[-1]


class Covid19API:

    CONFIRMEND_BY_DATE_URL = URL(
        r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    )

    def __init__(self):
        """ When initialized, requests data from the API and saves it in memory. """

        # Makes a request to the url, downloads data
        csv_content = self.__request(self.CONFIRMEND_BY_DATE_URL)

        self.__headers = csv_content[0]
        self.__content = self.__merge_content(csv_content[1:])

    # - - H E L P I N G - M E T H O D S - - #

    def __request(self,
                  url: URL,
                  ) -> typing.Tuple[typing.List[str],
                                    typing.List[typing.List[str]]
                                    ]:
        """ Make an http request for an csv API.
        Returns the data as a list of lists, where each element is a string.
        """

        response = requests.get(url=url.as_string())

        # Check if data loaded correctly
        if response.status_code != 200:
            raise RequestAPIError(
                f"{url}:\nResponse status {response.status_code}.")

        # convert downloaded content (in binary) to a 2d list with rows and
        # columns not very efficient, saves the whole downloaded spreadsheet
        # in memory until the object is deleted.... it is what it is (:

        decoded_content = response.content.decode('utf8').splitlines()
        sheet_content = list(csv.reader(decoded_content))

        return sheet_content

    def __change_types_row(self,
                           row: typing.List[str]
                           ) -> typing.List[typing.Union[str, int, float, None]]:
        """ By default, data is provided in a list of strings. This methods
        recives one row of data, and for each element in the row, converts
        it into an integer or a float. """

        new_row = list()
        for item in row:

            try:
                item = int(item)

            except ValueError:

                try:
                    item = float(item)

                except ValueError:
                    pass

            new_row.append(item)

        return new_row

    def __merge_content(self,
                        content: typing.List[typing.List[str]],
                        ) -> typing.List[typing.List[str]]:
        """ Some countries separate their data into different states or provinces,
        like Canada, the UK, and Australia. This method recives the data as is,
        and merges the seperated data. """

        new_content = list()
        visited_countries = set()

        for data_row in content:

            data_row = self.__change_types_row(data_row)
            country = self._country_from_row(data_row)

            if country in visited_countries:

                # find the index of the already saved data
                matching_index = next(
                    index
                    for index, row in enumerate(new_content)
                    if self._country_from_row(row) == country
                )

                # pop the already saved data from the database
                data_visited = new_content.pop(matching_index)

                # merge the rows
                data_row = self.__merge_rows(
                    data_row, data_visited,
                )

            # add the data to the new database,
            # save the current country as 'visited'
            new_content.append(data_row)
            visited_countries.add(country)

        return new_content

    def __merge_rows(self,
                     row_one: typing.List[str],
                     row_two: typing.List[str]
                     ) -> typing.List[str]:
        """ Recives two data rows from the database, and returns a single row
        that combines the data from both rows. Used in the `merge_content`
        method. """

        new_row = list()

        # iterate over rows
        for cur_one, cur_two in zip(row_one, row_two):

            if type(cur_one) != type(cur_two):
                cur_new = None

            else:

                if isinstance(cur_two, int):
                    cur_new = cur_one + cur_two

                elif isinstance(cur_two, float):
                    # not the 'real' average if used more then once on the
                    # same line, but it's better then nothing. This is used
                    # for the 'Lat' and 'Long' fields, but our script doesn't
                    # relay on those fields so I don't really care if it's
                    # not that accurate. (:
                    cur_new = (cur_one + cur_two) / 2

                else:

                    if cur_one == cur_two:
                        cur_new = cur_one

                    else:
                        cur_new = None

            new_row.append(cur_new)

        return new_row

    # - - R O W - M A N I P U L A T I O N - #

    def _confirmed_list_from_row(self,
                                 row: typing.List[typing.Union[
                                     str, int, float, None,
                                 ]],
                                 ) -> typing.List[int]:
        """ Recives a row from the database(that represents a country) and
        returns a list that represents the confirmed cases each day in the
        country, where the first number is the confirmed cases in the 22nd
        of January 2020, and the last element is the confirmend cases today.
        """

        # The non data fields (country name, state, etc.) always appear in the
        # 'left' (first elements in the list), so its very easy to cut them
        # out!

        NON_DATA_FIELDS = 4
        return row[NON_DATA_FIELDS:]

    def __find_field_in_row(self,
                            row: typing.List[typing.Union[
                                str, int, float, None,
                            ]],
                            field: str,
                            ) -> str:
        """ Recives a row from the database(that represents a country) and
        a field name. Returns the value of the given row in the given field. """

        if field not in self.__headers:
            raise ValueError("Invalid field")

        index = self.__headers.index(field)
        return row[index]

    def _country_from_row(self,
                          row: typing.List[typing.Union[
                              str, int, float, None,
                          ]],
                          ) -> str:
        """ Recives a row from the database(that represents a country),
        and returns the 'Country' field. """
        return self.__find_field_in_row(row, 'Country/Region')

    def _province_from_row(self,
                           row: typing.List[typing.Union[
                               str, int, float, None,
                           ]],
                           ) -> typing.Optional[str]:
        """ Recives a row from the database(that represents a country),
        and returns the 'Province/State' field. """
        return self.__find_field_in_row(row, 'Province/State')

    def _lat_from_row(self,
                      row: typing.List[typing.Union[
                          str, int, float, None,
                      ]],
                      ) -> typing.Optional[float]:
        """ Recives a row from the database(that represents a country),
        and returns the 'Lat' field. """
        return self.__find_field_in_row(row, 'Lat')

    def _long_from_row(self,
                       row: typing.List[typing.Union[
                           str, int, float, None,
                       ]],
                       ) -> typing.Optional[float]:
        """ Recives a row from the database(that represents a country),
        and returns the 'Long' field. """
        return self.__find_field_in_row(row, 'Long')

    # - - P U B L I C - M E T H O D S - - #

    def save_to_csv(self, path: str):
        """ Saves the data into a spreadsheet in the given file path, after
        the script analysed and modified it. """

        with open(path, 'w+', newline='') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows([self.__headers] + self.__content)

    def countries(self,) -> typing.Set[str]:
        """ All of the countries that are provided with the API.
        Returns a set of strings. """

        return {
            self._country_from_row(row)
            for row in self.__content
        }

    def get_country(self, country: str):
        """ Returns an `CovidCountryAPI` with data that represents the provided
        country only. """

        if country not in self.countries():
            raise ValueError("Invalid country")

        country_data = next(
            row for row in self.__content
            if self._country_from_row(row) == country
        )

        return CountryAPI(
            name=self._country_from_row(country_data),
            province=self._province_from_row(country_data),
            lat=self._lat_from_row(country_data),
            long=self._long_from_row(country_data),
            confirmed_each_day=self._confirmed_list_from_row(country_data),
        )


# - - E X C E P T I O N S - - #

class APIError(Exception):
    """ Raised when there is some sort of error while using the API """


class RequestAPIError(APIError):
    """ Raised when trying to pull data from the online API,
    but recives an error. """

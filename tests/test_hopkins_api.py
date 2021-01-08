from hopkins_api import CovidHistoryDatabase, CountryData
import typing


class TestHopkinsAPI:

    __API_INSTANCE = None
    __COUNTRIES = None

    @classmethod
    def __get_api_instance(cls) -> CovidHistoryDatabase:
        """ Returns an `CovidHistoryDatabase` instance. """

        if cls.__API_INSTANCE is None:
            cls.__API_INSTANCE = CovidHistoryDatabase()

        return cls.__API_INSTANCE

    @classmethod
    def __get_countries(cls) -> typing.List[CountryData]:
        """ Returns a set containing all of the countries from the API. """

        if cls.__COUNTRIES is None:
            api = cls.__get_api_instance()
            cls.__COUNTRIES = [
                api.country(country)
                for country in api.countries()
            ]

        return cls.__COUNTRIES

    def __assert_monotonic(self, list_of_nums: list, up: bool = True):
        """ Returns `False` only if the list is not ordered from lowest to
        highest, or from highest to lowest if `up` is set to `False`. """

        if len(list_of_nums) < 2:
            return True

        for index in range(1, len(list_of_nums)):
            cur = list_of_nums[index]
            prev = list_of_nums[index - 1]

            if not (cur == prev or (up == (cur > prev))):
                return False

        return True

    def test_countries(self,):
        api = self.__get_api_instance()
        countries = api.countries()

        assert isinstance(countries, list)
        for country in countries:
            assert isinstance(country, str), "Country name must be a string"
            assert country, "Must be a non-empty string"

        assert len(countries) >= 191
        # The number of countries in the database when the test was designed
        # Now, there may be more then 191 countries supported!

    def test_get_country(self,):
        countries = self.__get_countries()

        assert countries is not None, "Must be a list of CountryAPI instances"
        assert countries, "Must be a not empty"

        for country in countries:
            assert isinstance(
                country, CountryData), "Must be a CountryAPI instance"

    def test_country_name(self,):
        api = self.__get_api_instance()

        for country in self.__get_countries():
            assert isinstance(country.name, str)
            assert country.name in api.countries()
            assert country.name, "Must be a non-empty string"

    def __test_country_each_day_data(self, property: typing.Callable):

        for country in self.__get_countries():

            history_list = country.confirmed_each_day
            assert isinstance(history_list, list)

            assert len(history_list) > 100
            # list should be much longer then 100...

            for item in history_list:
                assert isinstance(item, int)

    def test_country_confirmed_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.confirmed_each_day
        )

    def test_country_deaths_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.deaths_each_day
        )

    def test_country_recovered_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.recovered_each_day
        )

    def test_country_total_confirmed_cases(self,):

        for country in self.__get_countries():
            assert isinstance(country.total_confirmed_cases, int)

    def test_country_new_cases(self,):

        for country in self.__get_countries():
            assert isinstance(country.new_cases, int)

    def test_country_new_cases_each_day(self,):

        for country in self.__get_countries():
            new_cases_list = country.new_cases_each_day

            assert isinstance(new_cases_list, list)
            assert len(new_cases_list) > 100

            for item in new_cases_list:
                assert isinstance(item, int)

    def test_country_new_cases_weekly_averages(self,):

        for country in self.__get_countries():
            weekly_averages_list = country.new_cases_weekly_averages

            assert isinstance(weekly_averages_list, list)
            assert len(weekly_averages_list) > 100

            for item in weekly_averages_list:
                assert isinstance(item, float)

    def test_country_r_values_each_day(self,):

        for country in self.__get_countries():
            r_values = country.r_values_each_day

            assert isinstance(r_values, list)
            assert len(r_values) > 100

            for item in r_values:
                assert isinstance(item, float)
                assert 0 <= item <= 50

    def test_country_r_value(self,):

        for country in self.__get_countries():
            assert isinstance(country.r_value, float)
            assert 0 <= country.r_value <= 50

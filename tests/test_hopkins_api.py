from hopkins_api import CovidHistoryDatabase, CountryData
import typing


class TestHopkinsAPI:

    __API_INSTANCE = None
    __COUNTRIES = None

    # - - Helpers - - #

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

    def __test_country_each_day_data(self, property_func: typing.Callable):

        for country in self.__get_countries():

            history_list = property_func(country)
            assert isinstance(history_list, list)

            assert len(history_list) > 100
            # list should be much longer then 100...

            for item in history_list:
                assert isinstance(item, int)

    def __test_country_property_int(self, property_func: typing.Callable):

        for country in self.__get_countries():
            value = property_func(country)
            assert isinstance(value, int), "This property must be an integer"

    # - - General - - #

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

    # - - Confirmed - - #

    def test_country_confirmed_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.confirmed_each_day
        )

    def test_country_confirmed(self,):
        self.__test_country_property_int(
            lambda country: country.confirmed
        )

    def test_country_confirmed_yesterday(self,):
        self.__test_country_property_int(
            lambda country: country.confirmed_yesterday
        )

    # - - Deaths - - #

    def test_country_deaths_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.deaths_each_day
        )

    def test_country_deaths(self,):
        self.__test_country_property_int(
            lambda country: country.deaths
        )

    def test_country_deaths_yesterday(self,):
        self.__test_country_property_int(
            lambda country: country.deaths_yesterday
        )

    def test_country_deaths_diff_today(self,):
        self.__test_country_property_int(
            lambda country: country.deaths_diff_today
        )

    # - - Recovered - - #

    def test_country_recovered_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.recovered_each_day
        )

    def test_country_recovered(self,):
        self.__test_country_property_int(
            lambda country: country.recovered
        )

    def test_country_recovered_yesterday(self,):
        self.__test_country_property_int(
            lambda country: country.recovered_yesterday
        )

    def test_country_recovered_diff_today(self,):
        self.__test_country_property_int(
            lambda country: country.recovered_diff_today
        )

    # - - Active cases - - #

    def test_country_active_each_day(self,):
        self.__test_country_each_day_data(
            lambda country: country.active_each_day
        )

    def test_country_active(self,):
        self.__test_country_property_int(
            lambda country: country.active
        )

    def test_country_active_yesterday(self,):
        self.__test_country_property_int(
            lambda country: country.active_yesterday
        )

    def test_country_active_diff_today(self,):
        self.__test_country_property_int(
            lambda country: country.active_diff_today
        )

    # - - New cases (confirmed diff) - - #

    def test_country_new_cases_each_day(self,):

        for country in self.__get_countries():
            new_cases_list = country.new_cases_each_day

            assert isinstance(new_cases_list, list)
            assert len(new_cases_list) > 100

            for item in new_cases_list:
                assert isinstance(item, int)

    def test_country_new_cases(self,):
        self.__test_country_property_int(
            lambda country: country.new_cases
        )

    def test_country_new_cases_yesterday(self,):
        self.__test_country_property_int(
            lambda country: country.new_cases_yesterday
        )

    def test_country_new_cases_weekly_averages(self,):

        for country in self.__get_countries():
            weekly_averages_list = country.new_cases_weekly_averages

            assert isinstance(weekly_averages_list, list)
            assert len(weekly_averages_list) > 100

            for item in weekly_averages_list:
                assert isinstance(item, float)

    # - - R values - - #

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

    def test_country_r_value_yesterday(self,):

        for country in self.__get_countries():
            assert isinstance(country.r_value_yesterday, float)
            assert 0 <= country.r_value <= 50

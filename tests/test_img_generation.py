import pytest
from PIL.Image import Image

from main import CovidStatsInstagramBot


class TestImageResult:

    @staticmethod
    def _test_image(img: Image):
        """ Recives a PIL image instace, and checks if the image is an actual
        image. """

        assert isinstance(img, Image)
        assert img.mode in {'RGB', 'RGBA'}

        width, height = img.size
        assert width >= 1000
        assert height >= 1000

    @pytest.mark.parametrize(
        'country',
        {'il', 'it', 'fr', 'jp', 'de', 'gb'},  # random country codes
    )
    def test_country_image(self, country: str,):
        """ Generates the covid stats image for Israel and tests if the image
        is generated correctly. """

        api = CovidStatsInstagramBot(country, 'What are you doing here?')
        self._test_image(api.to_image())

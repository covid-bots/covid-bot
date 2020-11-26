from typing import Tuple, List
from PIL import Image, ImageDraw, ImageFont
import math
from os import path, listdir
import random


class ImageGenerator:

    BACKGROUND_COLORS = {
        0:      (105, 191, 226),
        100:    (105, 226, 185),
        250:    (111, 226, 105),
        500:    (168, 226, 105),
        1_000:  (246, 171, 65),
        2_500:  (246, 120, 65),
        5_000:  (246, 65,  65),
        10_000: (140, 29,  20),
    }

    ASSETS_FOLDER = path.join("assets")
    RANDOM_BACKGROUND_IMAGES_FOLDER = path.join(ASSETS_FOLDER, "backgrounds")

    # - - - T I T L E S - A N D - V A L U E S - - - #

    TITLE_COLOR = (255, 255, 255, 255)
    VALUE_COLOR = (255, 255, 255, 255)
    SUBTITLE_COLOR = (255, 255, 255, 255)

    VALUE_TITLE_RATIO = 1.5  # value is 1.5 times bigger then title
    BIG_TITLE_SIZE = 200
    SMALL_TITLE_SIZE = 100

    BIG_TITLE_Y = 350
    SMALL_TITLES_Y = 850

    PADDING_BETWEEN_TITLES = 350
    MAX_SMALL_TITLES_IN_LINE = 3

    # - - -  F O N T S  - - - #

    FONTS_FOLDER = path.join(ASSETS_FOLDER, "fonts")
    TITLE_FONT_PATH = path.join(FONTS_FOLDER, "Heebo-Medium.ttf")
    VALUE_FONT_PATH = path.join(FONTS_FOLDER, "Heebo-Black.ttf")
    SUBTITLE_FONT_PATH = path.join(FONTS_FOLDER, "Heebo-Medium.ttf")

    # Load fonts
    BIG_TITLE_FONT = ImageFont.truetype(
        TITLE_FONT_PATH, size=BIG_TITLE_SIZE)
    BIG_VALUE_FONT = ImageFont.truetype(
        VALUE_FONT_PATH, size=int(BIG_TITLE_SIZE * VALUE_TITLE_RATIO))
    SMALL_TITLE_FONT = ImageFont.truetype(
        TITLE_FONT_PATH, size=SMALL_TITLE_SIZE)
    SMALL_VALUE_FONT = ImageFont.truetype(
        VALUE_FONT_PATH, size=int(SMALL_TITLE_SIZE * VALUE_TITLE_RATIO))
    SMALL_SUBTITLE_FONT = ImageFont.truetype(
        SUBTITLE_FONT_PATH, size=int(SMALL_TITLE_SIZE / VALUE_TITLE_RATIO))

    @classmethod
    def add_big_title(cls, base_img: Image.Image, title: str, value: str):

        draw = ImageDraw.Draw(base_img)
        x = base_img.width / 2
        y = cls.BIG_TITLE_Y

        draw.text((x, y), text=title, fill=cls.TITLE_COLOR,
                  font=cls.BIG_TITLE_FONT, anchor="mm")

        y += cls.BIG_TITLE_SIZE

        draw.text((x, y), text=value, fill=cls.VALUE_COLOR,
                  font=cls.BIG_VALUE_FONT, anchor="mm")

    @classmethod
    def __add_small_title(cls, img: Image.Image, xy: Tuple[int, int], title: str, value: str, subtitle: str):

        draw = ImageDraw.Draw(img)

        x, y = xy

        draw.text((x, y), text=title, fill=cls.TITLE_COLOR,
                  font=cls.SMALL_TITLE_FONT, anchor="mm")

        y += cls.SMALL_TITLE_SIZE * 1.2

        draw.text((x, y), text=value, fill=cls.VALUE_COLOR,
                  font=cls.SMALL_VALUE_FONT, anchor="mm")

        y += cls.SMALL_TITLE_SIZE

        draw.text((x, y), text=subtitle, fill=cls.SUBTITLE_COLOR,
                  font=cls.SMALL_SUBTITLE_FONT, anchor="mm")

    @classmethod
    def add_small_titles_row(cls,
                             img: Image.Image,
                             titles_list: List[int],
                             values_list: List[int],
                             subtitles_list: List[int],
                             ):
        x_jumps = img.width / len(titles_list)
        x = x_jumps / 2
        y = cls.SMALL_TITLES_Y

        for title, value, subtitle in zip(titles_list, values_list, subtitles_list):
            cls.__add_small_title(img, (x, y), title, value, subtitle)
            x += x_jumps

    @classmethod
    def generate_base_img(cls, new_cases: int):
        """ Returns an `Image` object that represents the background of the image. """

        # Choose random background
        files = listdir(cls.RANDOM_BACKGROUND_IMAGES_FOLDER)
        random_file = random.choice(files)

        # Load random background
        random_img = Image.open(
            path.join(cls.RANDOM_BACKGROUND_IMAGES_FOLDER, random_file))

        # Load background color image
        bg_color = cls.get_background_color(new_cases)
        background_img = Image.new("RGBA", random_img.size, color=bg_color)

        # Join two images
        return Image.alpha_composite(background_img, random_img)

    @classmethod
    def get_background_color(cls, new_cases: int):
        """ Returns a color that represents the number of new cases.
        If the number is high, the color will red, and if its low, it will slowly
        transform into orange -> yellow -> green -> blue.
        Uses the `cls.BACKGROUND_COLORS` dict
        """

        low_neighbor = None
        high_neighbor = None

        color_numbers = list(cls.BACKGROUND_COLORS.keys())
        color_numbers.sort()

        for cur_color_i, cur_color_num in enumerate(color_numbers):
            if new_cases <= cur_color_num:
                low_neighbor = cur_color_i - 1
                break

        # If the given num is lower then the minimum color num
        if cur_color_i == -1:
            return color_numbers[0]

        # If the given num is higher then the maximum color num
        if low_neighbor == None:
            return color_numbers[-1]

        # - - - - - - - - - - - - - - - - - - - #
        # If the given num is somewhere between #

        high_neighbor = color_numbers[low_neighbor + 1]
        low_neighbor = color_numbers[low_neighbor]

        high_neighbor_color = cls.BACKGROUND_COLORS[high_neighbor]
        low_neighbor_color = cls.BACKGROUND_COLORS[low_neighbor]

        new_cases_fixed = new_cases - low_neighbor
        neighbors_delta = high_neighbor - low_neighbor

        high_neighbor_force = new_cases_fixed / neighbors_delta
        low_neighbor_force = 1 - high_neighbor_force

        new_color = [
            int(
                (low_color_elem * low_neighbor_force) +
                (high_color_elem * high_neighbor_force)
            )
            for low_color_elem, high_color_elem in zip(low_neighbor_color, high_neighbor_color)
        ]

        return tuple(new_color)

    @classmethod
    def test_background_gradint(cls, from_: int, to: int, jumps: int = 1):

        width = math.ceil((to - from_) / jumps)
        height = int(width / 5)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for cur_index, cur_color_num in enumerate(range(from_, to, jumps)):

            color = cls.get_background_color(cur_color_num)

            p1 = (cur_index, 0)
            p2 = (cur_index, height)

            draw.line([p1, p2], fill=color, width=1)

        return img

from typing import Tuple
from PIL import Image, ImageDraw
import math
from os import path, listdir
import random


class ImageGenerator:

    BACKGROUND_COLORS = {
        0:     (105, 191, 226),
        100:   (105, 226, 185),
        250:   (111, 226, 105),
        500:   (168, 226, 105),
        1000:  (246, 171, 65),
        2500:  (246, 120, 65),
        5000:  (246, 65,  65),
        10000: (140, 29,  20),
    }

    RANDOM_BACKGROUND_IMAGES_FOLDER = path.join("assets", "backgrounds")

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

from typing import Tuple
from PIL import Image, ImageDraw
import math


class ImageGenerator:

    BACKGROUND_COLORS = {
        0: {
            "r": 105,
            "g": 191,
            "b": 226,
        },
        100: {
            "r": 105,
            "g": 226,
            "b": 185,
        },
        250: {
            "r": 111,
            "g": 226,
            "b": 105,
        },
        500: {
            "r": 168,
            "g": 226,
            "b": 105,
        },
        1000: {
            "r": 246,
            "g": 171,
            "b": 65,
        },
        2500: {
            "r": 246,
            "g": 120,
            "b": 65,
        },
        5000: {
            "r": 246,
            "g": 65,
            "b": 65,
        },
        10000: {
            "r": 140,
            "g": 29,
            "b": 20,
        }
    }

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

        return {color_key:
                int(
                    (low_neighbor_color[color_key] * low_neighbor_force) +
                    (high_neighbor_color[color_key] * high_neighbor_force)
                )
                for color_key in low_neighbor_color.keys()
                }

    @classmethod
    def test_background_gradint(cls, from_: int, to: int, jumps: int = 1):

        width = math.ceil((to - from_) / jumps)
        height = int(width / 5)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for cur_index, cur_color_num in enumerate(range(from_, to, jumps)):

            color = cls.get_background_color(cur_color_num)
            color_tuple = (color["r"], color["g"], color["b"])

            p1 = (cur_index, 0)
            p2 = (cur_index, height)

            draw.line([p1, p2], fill=color_tuple, width=1)

        return img


ImageGenerator.test_background_gradint(0, 5000).show()

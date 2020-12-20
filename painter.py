# Built in modules
from bidi.algorithm import get_display
from typing import Tuple, List, Optional
import math
import os
import random
import logging

# Pillow
from PIL import Image, ImageDraw, ImageFont, ImageOps

# Mathplotlib
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as font_manager
import pylab

# My code
from translator import StringManager
from grapher import GraphGenerator

logger = logging.getLogger(__name__)


class PosterText:
    """
    Represents a collection of words, sencenses, or lines. Has a method called
    `to_image` that generates a special image of the words, where each of the
    words has the same width.

    Has two main methods:
    ---------------------
    1.  `set_truetype_font()` - sets the font of the poster
    2.  `to_image()` - generates the poster image
    """

    def __init__(
            self,
            *arguments: List,
            string_manager=StringManager()
    ):
        self.set_string_manager(string_manager)
        self._lines = self.__arguments_to_lines(arguments)
        self._font_args = list()
        self._font_kwargs = list()

    def set_string_manager(self, sm: StringManager) -> None:
        if not isinstance(sm, StringManager):
            raise TypeError(
                "Argument must be an instance of the `StringManager` object.")
        self._string_manager = sm

    def __arguments_to_lines(self, arguments: List):
        """ Recives a list of arguments.
        Saves the strings and the lists only! """

        lines = list()
        for argument in arguments:
            if isinstance(argument, str):
                lines.append(argument)
            elif isinstance(argument, list):
                lines += argument
            else:
                logger.warning(
                    f"{argument} is not a supported argument. Ignoring...")

        return [get_display(line) for line in lines]

    def set_truetype_font(self, *args, **kwargs):
        """ Saves the argument and keyword arguments that are passed, and uses
        them when generating the font of the poster image. """

        if "size" in kwargs:
            logger.warning(
                "Setting a poster font should not receive a size. Ignoring...")
            del kwargs["size"]

        self._font_args = args
        self._font_kwargs = kwargs

    def __build_font(self, size: int):
        """ Returns a font object, with the given size. """

        return ImageFont.truetype(*self._font_args, **self._font_kwargs, size=size)

    def __check_font_size(self,
                          font: ImageFont.ImageFont,
                          text: str,
                          target_size: int,
                          match_area: float = 1,
                          ) -> int:
        """ Returns `-1`, `0` or `1` depending on the relation between the given
        `target_size` and the actual size of the given font.

        *  1  - if the font is LARGER then the target value
        *  0  - if the font size and the target value are the same
        * -1  - if the font is SMALLER then the target value
        """

        width = font.getsize(text)[0]
        if abs(target_size - width) <= match_area:
            return 0   # a match
        elif width > target_size:
            return 1   # font is LARGER then expected
        else:
            return -1  # font is SMALLER then expected

    def __get_font(self,
                   text: str,
                   target_size: int,
                   min_size: int = 1,
                   max_size: int = None,
                   ) -> ImageFont.ImageFont:
        """ Recives the text, and returns a font object that matches the given text,
        with the matching size. """

        if max_size is None:

            new_size = min_size * 2
            font = self.__build_font(new_size)
            if self.__check_font_size(font, text, target_size) == -1:
                # if the generated font is smaller then needed
                return self.__get_font(text, target_size, min_size=new_size)
            else:
                # if larger (or equal)
                return self.__get_font(text, target_size,
                                       min_size=min_size, max_size=new_size)

        else:
            # If both min and max values are given

            new_size = int(sum([max_size, min_size]) / 2)
            font = self.__build_font(new_size)

            if (self.__check_font_size(font, text, target_size) == 0
                    or abs(min_size-max_size) <= 1):
                # a match found! return the current font
                return font

            elif self.__check_font_size(font, text, target_size) == -1:
                # if the generated font is smaller then needed
                return self.__get_font(text, target_size,
                                       min_size=new_size, max_size=max_size)

            elif self.__check_font_size(font, text, target_size) == 1:
                # if the generated font is larger then needed
                return self.__get_font(text, target_size,
                                       min_size=min_size, max_size=new_size)

    def to_image(self, width: int, padding: int = 0, color="black",):
        """ Generates and returns a PIL image object, representing the poster text. """
        return self.__to_image(
            width=width,
            padding=padding,
            color=color,
            left_lines=self._lines,
            cur_height=0,
        )

    def __to_image(self,
                   width: int,
                   padding: int,
                   color,

                   # recursize arguments
                   left_lines: List[str],
                   cur_height: int,
                   ):

        if len(left_lines) == 0:
            # Generate the image - empty transparent
            return Image.new("RGBA", (width, cur_height), color=(255, 255, 255, 0))

        line = left_lines.pop(0)
        font = self.__get_font(text=line, target_size=width)

        height = font.getsize(line)[1]
        if left_lines:
            # If current line is not the last one
            height += padding

        image = self.__to_image(
            width=width,
            padding=padding,
            color=color,
            left_lines=left_lines,
            cur_height=cur_height + height,
        )
        draw = ImageDraw.Draw(image)
        draw.text((0, cur_height), line, fill=color, font=font)
        return image


class SingleDataPoster:

    ASSETS_PATH = os.path.join("assets", "icons")
    NO_CHANGE_ICON = Image.open(os.path.join(ASSETS_PATH, "no-change.png"))
    ARROW_UP_ICON = Image.open(os.path.join(ASSETS_PATH, "arrow-up.png"))
    ARROW_DOWN_ICON = ImageOps.flip(ARROW_UP_ICON)

    def __init__(self,
                 title: str,
                 now: int,
                 prev: int,
                 string_manager: StringManager = StringManager(),
                 ):
        self._title = title
        self._now = now
        self._prev = prev

        self.set_string_manager(string_manager)

    def set_string_manager(self, sm: StringManager) -> None:
        if not isinstance(sm, StringManager):
            raise TypeError(
                "Argument must be an instance of the `StringManager` object.")
        self._string_manager = sm

    @property
    def title(self,) -> str:
        return self._title

    @property
    def now(self,) -> int:
        return self._now

    @property
    def prev(self,) -> int:
        return self._prev

    @property
    def delta(self,) -> int:
        return self.now - self.prev

    @property
    def delta_str(self,) -> str:
        num = self.now - self.prev
        if num == 0:
            return self._string_manager.unchanged
        elif num > 0:
            return f"+{num}"
        else:
            return str(num)  # automatically adds the `-` sign

    @property
    def delta_precentage(self,) -> float:
        if self.prev == 0:
            return None

        one_precentage = self.prev / 100
        return self.delta / one_precentage

    @property
    def delta_precentage_str(self,):
        if self.delta_precentage is None:
            return self._string_manager.unavailable
        return f"{abs(self.delta_precentage):.1f}%"

    def to_image(self,
                 data_font: ImageFont.ImageFont,
                 title_font: ImageFont.ImageFont = None,
                 alter_font: ImageFont.ImageFont = None,

                 width=None,  # None = calculate automatically
                 color="black",

                 pad_title: int = 0,
                 pad_data: int = 0,

                 draw_line: bool = True,
                 line_length: int = None,  # None = max width.
                 line_width: int = 1,

                 icon_size: int = None,  # None = do not resize
                 pad_icon: int = 0,  # padding between icon and alter text
                 ):

        if title_font is None:
            title_font = data_font
        if alter_font is None:
            alter_font = data_font

        if width is None:
            width = self.__calc_image_width(
                data_font=data_font,
                title_font=title_font,
                alter_font=alter_font,
                draw_line=draw_line,
                line_length=line_length,
                icon_size=icon_size,
                pad_icon=pad_icon,
            )

        height = self.__calc_image_height(
            data_font=data_font,
            title_font=title_font,
            alter_font=alter_font,
            pad_title=pad_title,
            pad_data=pad_data,
            icon_size=icon_size,
        )

        # Create the image
        image = Image.new("RGBA", size=(width, height),
                          color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        x, y = int(width/2), 0

        # Add title to image
        draw.text((x, y), get_display(self.title),
                  font=title_font, fill=color, anchor="ma")
        y += title_font.getsize(self.title)[1]
        y += pad_title

        # Add data to image
        draw.text((x, y), str(self.now), font=data_font,
                  fill=color, anchor="ma")
        y += data_font.getsize(str(self.now))[1]
        y += int(pad_data / 2)

        # Add line to image, if needed
        if draw_line:
            if line_length is None:
                line_x_start = 0
                line_x_end = width
            else:
                line_x_start = int((width - line_length) / 2)
                line_x_end = line_x_start + line_length

            draw.line((line_x_start, y, line_x_end, y),
                      fill=color, width=line_width)
        y += int(pad_data / 2)

        # Add alter data to image
        alter_img = self.alter_image(
            font=alter_font, color=color, icon_size=icon_size, pad_icon=pad_icon)
        x = int((width - alter_img.width) / 2)
        image.paste(alter_img, box=(x, y))

        return image

    def __calc_image_height(self,
                            data_font: ImageFont.ImageFont,
                            title_font: ImageFont.ImageFont,
                            alter_font: ImageFont.ImageFont,
                            pad_title: int,
                            pad_data: int,
                            icon_size: Optional[int]):
        alter_height = self.__calc_alter_height(
            font=alter_font, icon_size=icon_size
        )

        data_height = data_font.getsize(str(self.now))[1]
        title_height = title_font.getsize(self.title)[1]

        return math.ceil(sum([
            alter_height,
            data_height,
            title_height,
            pad_title,
            pad_data,
        ]))

    def alter_image(self,
                    font: ImageFont.ImageFont,
                    color="black",
                    icon_size: int = None,  # None = do not resize
                    pad_icon: int = 0,  # padding between icon and alter text
                    ):

        size = (self.__calc_alter_width(font=font, icon_size=icon_size, pad_icon=pad_icon),
                self.__calc_alter_height(font=font, icon_size=icon_size))

        image = Image.new("RGBA", color=(255, 255, 255, 0), size=size)

        # Load the icon
        icon = self.__get_matching_icon(color=color)
        if icon_size is not None:
            # Resize if needed
            if isinstance(icon_size, int):
                icon_size = (icon_size, icon_size)
            icon = icon.resize(icon_size)

        # Paste icon
        x = int(font.getsize(self.delta_str)[0] + pad_icon)
        y = int((image.height - icon.height) / 2)
        image.paste(icon, box=(x, y))

        # Generate draw object
        draw = ImageDraw.Draw(image)

        # Paste left text
        x = 0
        y = int(image.height / 2)
        draw.text((x, y), self.delta_str,
                  fill=color, font=font, anchor="lm")

        # Paste right text
        x = image.width
        draw.text((x, y), self.delta_precentage_str,
                  fill=color, font=font, anchor="rm")

        return image

    def __get_matching_icon(self, color=None,) -> Image.Image:
        if self.delta == 0:
            icon = self.NO_CHANGE_ICON.copy()
        elif self.delta > 0:
            icon = self.ARROW_UP_ICON.copy()
        else:
            icon = self.ARROW_DOWN_ICON.copy()

        # Add color to the icon
        if color is not None:
            color_img = Image.new("RGB", size=icon.size, color=color)
            color_img.putalpha(icon.getchannel('A'))
            icon = color_img

        return icon

    def __calc_alter_width(self,
                           font: ImageFont.ImageFont,
                           icon_size: int,  # None = do not resize
                           pad_icon: int,  # padding between icon and alter text
                           ) -> int:
        if icon_size is None:
            icon_size = self.ARROW_UP_ICON.width

        alter_width = icon_size
        alter_width += pad_icon * 2
        alter_width += font.getsize(self.delta_str)[0] + \
            font.getsize(self.delta_precentage_str)[0]

        return math.ceil(alter_width)

    def __calc_alter_height(self, font: ImageFont.ImageFont, icon_size: int) -> int:
        if icon_size is None:
            icon_size = self.__get_matching_icon().height

        return math.ceil(max(
            icon_size,
            font.getsize(self.delta_str)[1],
            font.getsize(self.delta_precentage_str)[1],
        ))

    def __calc_image_width(self,
                           data_font: ImageFont.ImageFont,
                           title_font: ImageFont.ImageFont,
                           alter_font: ImageFont.ImageFont,
                           draw_line: bool,
                           line_length: Optional[int],
                           icon_size: Optional[int],
                           pad_icon: int,
                           ) -> int:

        data_width = data_font.getsize(str(self.now))[0]
        title_width = title_font.getsize(self.title)[0]
        alter_width = self.__calc_alter_width(
            font=alter_font, icon_size=icon_size, pad_icon=pad_icon)

        if line_length is None:
            line_length = 0

        return math.ceil(max([
            data_width,
            title_width,
            line_length,
            alter_width,
        ]))


class ImageGenerator:

    ASSETS_FOLDER = "assets"
    FONTS_FOLDER = os.path.join(ASSETS_FOLDER, "fonts")

    POSTER_FONT_PATH = os.path.join(FONTS_FOLDER, "Heebo-Black.ttf")

    # Perecentage: values between 0 and 1,
    # where 1 is the whole width / height of the image.
    POSTER_WIDTH = 0.35  # 1 is the whole width
    POSTER_PADDING_FROM_SIDES = 0.275  # 1 is the whole width
    POSTER_PADDING_TITLES = -0.025    # 1 is the whole height

    ALTER_FONT = ImageFont.truetype(os.path.join(
        FONTS_FOLDER, 'Heebo-Medium.ttf'), size=50)
    TITLE_FONT = ImageFont.truetype(os.path.join(
        FONTS_FOLDER, 'Heebo-Medium.ttf'), size=75)
    DATA_FONT = ImageFont.truetype(os.path.join(
        FONTS_FOLDER, 'Heebo-Black.ttf'), size=100)

    DATA_PADDING_FROM_SIDES = 0.2  # Perecentage - 1 is the whole width of the image
    SUBTITLE_PADDING = 0.01
    SUBTITLE_FONT = ImageFont.truetype(os.path.join(
        FONTS_FOLDER, 'Heebo-Medium.ttf'), size=25)

    SINGLE_DATA_POSTER_ARGUMENTS = {
        "data_font": DATA_FONT,
        "title_font": TITLE_FONT,
        "alter_font": ALTER_FONT,

        "color": "white",
        "line_length": 400,
        "line_width": 5,

        "icon_size": 50,
        "pad_icon": 25,

        "pad_title": -25,
        "pad_data": 40,
    }

    BACKGROUND_COLORS = {
        # Keys are R values.
        # See method `get_background_color` for more information!
        0.50: (24,  205, 244),  # Light blue
        0.75: (113, 248, 90),   # Light green
        1.00: (191, 248, 18),   # Green, starts to became orange
        1.25: (248, 170, 18),   # Orange
        1.50: (247, 71,  36),   # Red
        1.75: (166, 25,  25),   # Dark red
    }

    def __init__(self,
                 base_img: Image.Image,
                 string_manager: StringManager = StringManager()
                 ):
        self._image = base_img
        self.set_string_manager(string_manager)

    def set_string_manager(self, sm: StringManager) -> None:
        if not isinstance(sm, StringManager):
            raise TypeError(
                "Argument must be an instance of the `StringManager` object.")
        self._string_manager = sm

    @property
    def image(self,):
        return self._image.copy()

    def add_background(self, r_value: float):
        background = Image.new("RGBA", size=self.image.size,
                               color=self._calc_color(r_value))
        background.alpha_composite(self.image)
        self._update_image(background)

    @classmethod
    def test_color_gradint(cls, from_: float, to: float, jumps: float = 0.01):

        width = math.ceil((to - from_) / jumps)
        height = int(width / 5)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for cur_pixel in range(width):

            cur_r = from_ + (jumps * cur_pixel)
            color = cls._calc_color(cur_r)

            p1 = (cur_pixel, 0)
            p2 = (cur_pixel, height)

            draw.line([p1, p2], fill=color, width=1)

        return img

    def add_poster_title(self,
                         poster: PosterText,

                         y_relative: float = 0.5,
                         # 0 is the top, 1/2 is the middle and 1 is the bottom.
                         # middle is the default (:

                         side: str = "m",
                         color: str = "black",
                         ):

        # Assert good `side` value
        if not isinstance(side, str):
            raise TypeError("Poster `side` should be a one character string.")
        if len(side) != 1:
            raise ValueError("Poster `side` should be a one character string.")

        # Set `x` value depending on the `side`
        if side == "l":
            x = self._precentage_of_width(self.POSTER_PADDING_FROM_SIDES)
        elif side == "m":
            x = self._precentage_of_width(0.5)
        elif side == "r":
            x = self.image.width - \
                self._precentage_of_width(self.POSTER_PADDING_FROM_SIDES)
        else:
            raise ValueError(
                "Poster `side` should be assembled using the characters `l` (left), `m` (middle) and `r` (right) only.")

        # Set font and string manager of title
        poster.set_truetype_font(self.POSTER_FONT_PATH)
        poster.set_string_manager(self._string_manager)

        # Generate poster image
        poster_img = poster.to_image(
            width=self._precentage_of_width(self.POSTER_WIDTH),
            padding=self._precentage_of_height(self.POSTER_PADDING_TITLES),
            color=color,
        )

        x -= int(poster_img.width / 2)
        y = self._precentage_of_height(y_relative) - int(poster_img.height / 2)

        img = self.image
        img.paste(poster_img, box=(x, y), mask=poster_img)
        self._update_image(img)

    def add_data(self,
                 data: List[SingleDataPoster],
                 start_relative_y: float,
                 end_relative_y: float,
                 ) -> None:

        start_y = self._precentage_of_height(start_relative_y)
        end_y = self._precentage_of_height(end_relative_y)
        height = end_y - start_y

        if len(data) > 1:
            pad = self._precentage_of_width(self.DATA_PADDING_FROM_SIDES)
            work_area = self.image.width - (pad * 2)
            jump = int(work_area / (len(data) - 1))
            x = pad
        else:
            jump = 0
            x = self._precentage_of_width(0.5)

        img = self.image

        for poster in data:
            poster.set_string_manager(self._string_manager)
            poster_img = poster.to_image(**self.SINGLE_DATA_POSTER_ARGUMENTS)
            poster_img = self.__resize_to_height(poster_img, height)

            color_img = Image.new(
                "RGB", size=poster_img.size, color=self.SINGLE_DATA_POSTER_ARGUMENTS["color"])

            paste_x = x - int(poster_img.width / 2)
            img.paste(color_img, box=(paste_x, start_y), mask=poster_img)

            x += jump

        self._update_image(img)

    def add_graph(self,
                  data: List[int],
                  r_value: float,
                  relative_size: Tuple[int],
                  relative_pos: Tuple[int],
                  title: str = None,
                  title_color=None,
                  accent_color="black",
                  ):

        size = tuple([self._precentage_of_width(cur) for cur in relative_size])
        pos = (
            self._precentage_of_width(relative_pos[0]),
            self._precentage_of_height(relative_pos[1])
        )

        graph_gen = GraphGenerator()
        graph_gen.set_title(title, title_color)

        graph_gen.add_data(
            data,
            min_color=accent_color,
            max_color=accent_color,
            color=self._calc_color(r_value),
        )

        base_img = self.image
        fig_mask = graph_gen.to_img(size=size)
        fig_img = fig_mask.convert('RGB')

        pos = [cur_pos - int((img_size / 2))
               for img_size, cur_pos in zip(size, pos)]

        base_img.paste(fig_img, box=pos, mask=fig_mask)
        self._update_image(base_img)

    def add_graph_r_values(self,
                           data: List[int],
                           r_value: float,
                           guide_color,
                           relative_size: Tuple[int],
                           relative_pos: Tuple[int],
                           title: str = None,
                           title_color=None,
                           accent_color="black",
                           ):

        size = tuple([self._precentage_of_width(cur) for cur in relative_size])
        pos = (
            self._precentage_of_width(relative_pos[0]),
            self._precentage_of_height(relative_pos[1])
        )

        graph_gen = GraphGenerator()
        graph_gen.set_title(title, title_color)

        graph_gen.add_data(
            data,
            color=self._calc_color(r_value),
            min_color=accent_color,
            max_color=accent_color,
        )

        graph_gen.add_guide_line(y=1, color=accent_color)

        base_img = self.image
        fig_mask = graph_gen.to_img(size=size)
        fig_img = fig_mask.convert('RGB')

        pos = [cur_pos - int((img_size / 2))
               for img_size, cur_pos in zip(size, pos)]

        base_img.paste(fig_img, box=pos, mask=fig_mask)
        self._update_image(base_img)

    def add_subtitle(self, string: str, color="black"):
        """ Adds a subtitle to the image. """

        padding = self._precentage_of_height(self.SUBTITLE_PADDING)
        font = self.SUBTITLE_FONT

        img = self.image
        draw = ImageDraw.Draw(img)
        size_x, size_y = img.size

        text_x = int(size_x / 2)
        text_y = size_y - padding

        draw.text((text_x, text_y), get_display(string),
                  font=font, fill=color, anchor="ms")

        self._update_image(img)

    # - - - P R I V A T E - A N D - P R O T E C T E D - - - #

    def _update_image(self, img: Image.Image):
        self._image = img

    def _precentage_of_width(self, value: float):
        return int(self._image.width * value)

    def _precentage_of_height(self, value: float):
        return int(self._image.height * value)

    @classmethod
    def _calc_color(cls, r_value: float):
        """ Returns a color that represents the current R value.
        If the R value is high, the color will red, and if its low, it will slowly
        transform into orange -> yellow -> green -> blue.
        Uses the `BACKGROUND_COLORS` dict
        """

        low_neighbor = None
        high_neighbor = None

        color_numbers = list(cls.BACKGROUND_COLORS.keys())
        color_numbers.sort()

        for cur_color_i, cur_color_num in enumerate(color_numbers):
            if r_value <= cur_color_num:
                low_neighbor = cur_color_i - 1
                break

        # If the given num is lower then the minimum color num
        if cur_color_i == 0:
            return cls.BACKGROUND_COLORS[color_numbers[0]]

        # If the given num is higher then the maximum color num
        if low_neighbor == None:
            return cls.BACKGROUND_COLORS[color_numbers[-1]]

        # - - - - - - - - - - - - - - - - - - - #
        # If the given num is somewhere between #

        high_neighbor = color_numbers[low_neighbor + 1]
        low_neighbor = color_numbers[low_neighbor]

        high_neighbor_color = cls.BACKGROUND_COLORS[high_neighbor]
        low_neighbor_color = cls.BACKGROUND_COLORS[low_neighbor]

        r_fixed = r_value - low_neighbor
        neighbors_delta = high_neighbor - low_neighbor

        high_neighbor_force = r_fixed / neighbors_delta
        low_neighbor_force = 1 - high_neighbor_force

        new_color = [
            int(
                (low_color_elem * low_neighbor_force) +
                (high_color_elem * high_neighbor_force)
            )
            for low_color_elem, high_color_elem in zip(low_neighbor_color, high_neighbor_color)
        ]

        return tuple(new_color)

    def __resize_to_height(self, img: Image.Image, height: int):
        """ Returns a copy of the given image, but resized so the image ratio
        stays the same, and the height of the new image equal the given height. """

        resize_factor = img.height / height
        new_width = int(img.width / resize_factor)
        return img.resize((new_width, height))

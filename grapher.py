import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
from bidi.algorithm import get_display
from PIL import Image
import os

from typing import Tuple, List, Union, Optional

from translator import StringManager


class GraphGenerator:

    GENERAL_LINES_CONFIG = {
        "linewidth": 5,
        "solid_capstyle": "round",
        "dash_capstyle": "round",
        "dash_joinstyle": "round",
    }

    GUIDE_LINES_CONFIG = {
        **GENERAL_LINES_CONFIG,
        "linestyle": "dashed",
    }

    MAIN_LINES_CONFIG = {
        **GENERAL_LINES_CONFIG,
        "linewidth": 7
    }

    MARKERS_CONFIG = {
        "zorder": 10,
        "s": 250,
    }

    TEXT_CONFIG = {
        "fontsize": "xx-large",
        "fontweight": "bold",
        "horizontalalignment": "center",
        "verticalalignment": "center",
    }

    TITLE_TEXT_CONFIG = {
        **TEXT_CONFIG,
        "pad": 50,
    }

    MARK_TEXT_OFFEST = 0.125  # relative to the height of the figure

    def __init__(self,
                 string_manager: StringManager = StringManager(),
                 ):
        self._data = list()
        self._guides = list()
        self._title = (None, None)

        self.set_string_manager(string_manager)

    def set_string_manager(self, sm: StringManager) -> None:
        if not isinstance(sm, StringManager):
            raise TypeError(
                "Argument must be an instance of the `StringManager` object.")
        self._string_manager = sm

    def add_data(self,
                 data: List[float],
                 color="black",
                 min_color=None,  # None = don't mark
                 max_color=None,
                 min_text="{y}",
                 max_text="{y}",
                 ) -> None:
        self._data.append({
            "data": data,
            "color": color,
            "min_color": min_color,
            "max_color": max_color,
            "min_text": min_text,
            "max_text": max_text,
        })

    def add_guide_line(self,
                       y: float,
                       color="red",
                       ) -> None:
        self._guides.append({
            "y": y,
            "color": color,
        })

    def _plot_data(self,
                   ax,
                   data,
                   color,
                   min_color,
                   max_color,
                   min_text,
                   max_text,
                   ) -> None:
        """ Plots the given data list to the figure. """

        x_list = [i for i in range(len(data))]
        self.__plot_line_with_gradient(ax=ax, x=x_list, y=data, color=color)

        min_y = min(data)
        max_y = max(data)
        range_y = max_y - min_y
        mark_titles_offset = range_y * self.MARK_TEXT_OFFEST

        # Add "markers" in the start and the end of the data
        self._mark_point(ax, point=(0, data[0]), color=color)
        self._mark_point(ax, point=(len(data) - 1, data[-1]), color=color)

        if min_color is not None:
            x = data.index(min_y)
            self._mark_point(ax, (x, min_y), color=min_color)
            self._mark_text_point(ax, (x, min_y), color=min_color,
                                  text=min_text, offset=-mark_titles_offset)

        if max_color is not None:
            x = data.index(max_y)
            self._mark_point(ax, (x, max_y), color=max_color)
            self._mark_text_point(ax, (x, max_y), color=max_color,
                                  text=max_text, offset=mark_titles_offset)

    def _plot_guide_line(self,
                         ax,
                         y: float,
                         color,
                         length,
                         ) -> None:
        """ Adds a guide line in the given Y value.
        The guild line is a dashed straight line! """

        x = [0, length - 1]
        y = [y] * 2

        config = {**self.GUIDE_LINES_CONFIG,
                  "color": self.__normalize_color(color),
                  }

        ax.plot(x, y, **config)

    def _plot_title(self, ax,):
        title, color = self._title
        if title is not None:
            ax.set_title(get_display(title),
                         **self.TITLE_TEXT_CONFIG,
                         color=color)

    def _generate(self):
        """ Generates the figure and returns a matplotlib `figure` instance. """

        fig, ax = self.__build_empty_fig()
        data_len = 0

        for data in self._data:
            data_len = max([data_len, len(data["data"])])
            self._plot_data(ax, **data)

        for guide in self._guides:
            self._plot_guide_line(ax, length=data_len, **guide)

        self._plot_title(ax)

        return fig, ax

    def to_img(self, temp_file_path: str = "fig.png", size=None,) -> Image.Image:
        self.save(temp_file_path, size=size,)
        return Image.open(temp_file_path)

    def set_title(self, title: Optional[str] = None, color=None):
        self._title = (title, color)

    def clear_title(self,):
        self.set_title(None)

    def save(self, filepath: str, size=None):
        """ Saves a clean version of the figure (without axes, transperant background). """

        fig, ax = self._generate()

        if size is not None:
            fig.set_size_inches(self.__pixels_to_inches(size))

        self.__config_ax(ax)
        fig.tight_layout()
        fig.savefig(filepath, transparent=True)

    def __plot_line_with_gradient(self, ax, x, y, color):
        """
        Plot a line with a linear alpha gradient filled beneath it.
        Edited from https://stackoverflow.com/a/29331211/10671845
        """

        config = {**self.MAIN_LINES_CONFIG,
                  "color": self.__normalize_color(color),
                  }

        line, = ax.plot(x, y, **config)
        color = line.get_color()

        alpha = line.get_alpha()
        alpha = 1.0 if alpha is None else alpha

        # Generate the gradient image
        z = np.empty((100, 1, 4), dtype=float)
        rgb = mcolors.colorConverter.to_rgb(color)
        z[:, :, :3] = rgb
        z[:, :, -1] = np.linspace(0, alpha, 100)[:, None]

        # Add the gradient image to the plot
        im = ax.imshow(z, aspect='auto', extent=[min(x), max(x), min(y), max(y)],
                       origin='lower',)

        # Add mask to the image, to appear only below the line plot
        xy = np.column_stack([x, y])
        xy = np.vstack(
            [[min(x), min(y)], xy, [max(x), min(y)], [min(x), min(y)]])
        clip_path = Polygon(xy, facecolor='none',
                            edgecolor='none', closed=True)
        ax.add_patch(clip_path)
        im.set_clip_path(clip_path)

    def __update_data_length(self, new_len: int):
        self._data_len = max(self._data_len, new_len)

    @staticmethod
    def __config_ax(ax):
        """ Removes the axis from a graph. """

        ax.axis(False)  # Hide axis
        ax.use_sticky_edges = False
        ax.margins(x=0.1, y=0.1)  # "Zoom out" 10%

    @staticmethod
    def __pixels_to_inches(px: Union[int, Tuple[int]]):

        if isinstance(px, int):
            return px / 100

        else:
            return tuple([
                cur / 100
                for cur in px
            ])

    @staticmethod
    def __normalize_color(color):
        """ Converts a color represented by 3 RGB numbers between 0 and 255 into
        a color represented with 3 floats between 0 and 1. """

        if isinstance(color, tuple):
            color = tuple([cur / 255 for cur in color])
        return color

    @staticmethod
    def __build_empty_fig():
        fig = plt.figure()
        ax = fig.add_subplot()
        return fig, ax

    @classmethod
    def _mark_point(cls, ax, point: Tuple[float], color="red"):
        config = {**cls.MARKERS_CONFIG,
                  "facecolor": cls.__normalize_color(color)}

        ax.scatter(
            x=point[0],
            y=point[1],
            **config,
        )

    def _mark_text_point(self,
                         ax,
                         point: Tuple[float],
                         color,
                         text: str,
                         offset: float,
                         ) -> None:
        x, y = point
        x_str = self._string_manager.format_number(x, floating_max=3)
        y_str = self._string_manager.format_number(y, floating_max=3)

        text = text.replace("{x}", x_str).replace("{y}", y_str)

        config = {**self.TEXT_CONFIG,
                  "x": x,
                  "y": y+offset,
                  "s": get_display(text),
                  "color": color,
                  }

        ax.text(**config)

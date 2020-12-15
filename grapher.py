import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon

from typing import Tuple, List


class GraphGenerator:

    GENERAL_LINES_CONFIG = {
        "linewidth": 5,
        "solid_capstyle": "round",
        "dash_capstyle": "round",
        "dash_joinstyle": "round",
    }

    GUIDE_LINES_CONFIG = {
        "linestyle": "dashed",
    }

    MAIN_LINES_CONFIG = {
    }

    @staticmethod
    def __pixels_to_inches(px: int):
        return px / 100

    @classmethod
    def plot_r_values(cls,
                      data: List,
                      size: Tuple[int] = (1000, 500),
                      color="black",
                      guide_color="red"
                      ):

        fig, ax = cls.__build_empty_fig(size)
        x_list = [i for i in range(len(data))]

        cls.__plot_line_with_gradient(x=x_list, y=data, ax=ax, color=color)
        cls.__plot_guide_line(x_list=x_list, y=1, ax=ax, color=guide_color)

        return fig

    @classmethod
    def plot_data(cls,
                  data,
                  size: Tuple[int] = (1000, 500),
                  color="black"
                  ):
        fig, ax = cls.__build_empty_fig(size)
        x_list = [i for i in range(len(data))]

        cls.__plot_line_with_gradient(x=x_list, y=data, ax=ax, color=color)
        return fig

    @classmethod
    def __build_empty_fig(cls, size_px: Tuple[int]):
        size = [cls.__pixels_to_inches(cur) for cur in size_px]
        fig = plt.figure(figsize=size)
        ax = fig.add_subplot()

        return fig, ax

    @classmethod
    def __plot_guide_line(cls, x_list: List, y, ax, color):

        GUIDE_LINES_CONFIG = {**cls.GENERAL_LINES_CONFIG,
                              **cls.GUIDE_LINES_CONFIG,
                              "color": color,
                              }
        y_list = [y] * len(x_list)
        ax.plot(x_list, y_list, **GUIDE_LINES_CONFIG)

    @classmethod
    def __plot_line_with_gradient(cls, x, y, ax, color):
        """
        Plot a line with a linear alpha gradient filled beneath it.
        Edited from https://stackoverflow.com/a/29331211/10671845
        """

        MAIN_LINES_CONFIG = {**cls.GENERAL_LINES_CONFIG,
                             **cls.MAIN_LINES_CONFIG,
                             "color": color,
                             }

        line, = ax.plot(x, y, **MAIN_LINES_CONFIG)
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

        return line, im

    @classmethod
    def save_clean(cls, figure, filepath):
        """ Saves a clean version of the figure (without axes, transperant background). """
        cls.remove_axis(figure)
        figure.savefig(filepath, transparent=True)

    @staticmethod
    def remove_axis(figure):
        """ Removes the axis from a graph. """
        for ax in figure.get_axes():
            ax.axis(False)

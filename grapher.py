import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon

from typing import Tuple


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

    def __init__(self, main_color, accent_color):
        self.MAIN_LINES_CONFIG["color"] = main_color
        self.GUIDE_LINES_CONFIG["color"] = accent_color

        self.MAIN_LINES_CONFIG = {
            **self.GENERAL_LINES_CONFIG, **self.MAIN_LINES_CONFIG}
        self.GUIDE_LINES_CONFIG = {
            **self.GENERAL_LINES_CONFIG, **self.GUIDE_LINES_CONFIG}

    @staticmethod
    def __pixels_to_inches(px: int):
        return px / 100

    def plot_r_values(self, data, size: Tuple[int] = (1000, 500)):

        # convert pixels to inches
        size = [self.__pixels_to_inches(cur) for cur in size]

        # Create a new figure
        fig = plt.figure(figsize=size)
        ax = fig.add_subplot()

        x_list = [i for i in range(len(data))]

        self.__plot_line_with_gradient(x=x_list, y=data, ax=ax,)
        self.__plot_guide_line(x_list=x_list, y=1, ax=ax,)

        return fig

    def __plot_guide_line(self, x_list, y, ax):
        y_list = [y] * len(x_list)
        ax.plot(x_list, y_list, **self.GUIDE_LINES_CONFIG)

    def __plot_line_with_gradient(self, x, y, ax):
        """
        Plot a line with a linear alpha gradient filled beneath it.
        Edited from https://stackoverflow.com/a/29331211/10671845
        """

        line, = ax.plot(x, y, **self.MAIN_LINES_CONFIG)
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

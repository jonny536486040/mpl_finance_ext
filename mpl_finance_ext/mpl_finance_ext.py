import matplotlib.pyplot as plt
import matplotlib.transforms as mtrans
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import BoxStyle
from matplotlib.patches import Polygon
import matplotlib.colors as mcolors
from six.moves import xrange, zip
from mpl_toolkits.mplot3d import Axes3D

from .angled_box_style import AngledBoxStyle
from .candlestick_pattern_evaluation import draw_pattern_evaluation
from .signal_evaluation import draw_signal_evaluation
from .signal_evaluation import draw_verticals

import logging
logger = logging.getLogger('mpl_finance_ext')

# Colors:
label_colors = '#c1c1c1'
accent_color = '#13bebc'
background_color = '#ffffff'

red = '#fe0000'  # '#fe0000'
green = '#00fc01'  # '#13bebc'

color_set = ['#13bebc', '#b0c113', '#c1139e', '#c17113', '#0d8382']

# Create angled box style
BoxStyle._style_list["angled"] = AngledBoxStyle


def _candlestick2_ohlc(
        ax, opens, highs, lows, closes,
        width=4.0, colorup=accent_color, colordown=label_colors,
        alpha=0.75, index_fix=True
):
    # Functions not supported in macOS
    # colorup = mcolors.to_rgba(colorup, alpha)
    # colordown = mcolors.to_rgba(colordown, alpha)
    line_colors = list()
    poly_colors_up = list()
    poly_colors_down = list()

    count = 0
    delta = width - 0.16
    poly_segments_up = list()
    poly_segments_down = list()
    line_segments = list()

    for i, open, close, high, low in zip(
            xrange(len(opens)), opens, closes, highs, lows):
        if index_fix:
            i = opens.index[count]
            count += 1
        if open != -1 and close != -1:
            # Simple modification to draw a line for open == close
            # if open == close:
            #     open -= 0.01 * abs(high - low)

            if close > open:
                poly_segments_up.append(
                    ((i - delta, open), (i - delta, close),
                     (i + delta, close), (i + delta, open))
                )
                poly_colors_up.append(colorup)
                if close < high:
                    line_segments.append(((i, close), (i, high)))
                    line_colors.append(colorup)
                if low < open:
                    line_segments.append(((i, low), (i, open)))
                    line_colors.append(colorup)

            else:
                poly_segments_down.append(
                    ((i - delta, open), (i - delta, close),
                     (i + delta, close), (i + delta, open))
                )
                poly_colors_down.append(colordown)
                if open < high:
                    line_segments.append(((i, open), (i, high)))
                    line_colors.append(colordown)
                if low < close:
                    line_segments.append(((i, low), (i, close)))
                    line_colors.append(colordown)

    use_aa = 0,  # use tuple here
    line_collection = LineCollection(
        line_segments,
        colors=line_colors,
        linewidths=0.7,
        antialiaseds=use_aa,
        linestyles='solid'
    )

    bar_collection_down = PolyCollection(
        poly_segments_down,
        facecolors=label_colors,
        edgecolors=poly_colors_down,
        antialiaseds=use_aa,
        linewidths=0,
    )

    bar_collection_up = PolyCollection(
        poly_segments_up,
        facecolors=accent_color,
        edgecolors=poly_colors_up,
        antialiaseds=use_aa,
        linewidths=0,
    )

    if index_fix:
        minx, maxx = closes.index[0], closes.index[-1]
    else:
        minx, maxx = 0, len(line_segments)

    miny = min([low for low in lows if low != -1])
    maxy = max([high for high in highs if high != -1])

    corners = (minx, miny), (maxx, maxy)
    ax.update_datalim(corners)
    ax.autoscale_view()

    ax.add_collection(line_collection)
    ax.add_collection(bar_collection_up)
    ax.add_collection(bar_collection_down)
    return line_collection, bar_collection_up, bar_collection_down


def _add_text_box(fig, axis, text, x_p, y_p):
    x = axis.get_xlim()
    y = axis.get_ylim()
    text_x = x[0] / 100 * x_p
    text_y = y[1] / 100 * y_p

    trans_offset = mtrans.offset_copy(
        axis.transData,
        fig=fig,
        x=0.0,
        y=0.0,
        units='inches'
    )

    axis.text(text_x, text_y, text, ha='left', va='center',
              transform=trans_offset, color='#535353',
              bbox=dict(alpha=0.4, color=label_colors))


def _vspan(kwa, ax):
    # Vertical span and lines:
    vlines = kwa.get('vline', None)
    if vlines is not None:
        linestyle = '--'
        color = color_set[0]
        linewidth = 0.8
        alpha = 0.8
        for vline in vlines:

            if 'color' in vline:
                color = vline['color']

            if 'linewidth' in vline:
                linewidth = vline['linewidth']

            if 'linestyle' in vline:
                linestyle = vline['linestyle']

            if 'alpha' in vline:
                alpha = vline['alpha']

            plot_vline(
                axis=ax, index=vline['ix'],
                linestyle=linestyle,
                color=color, linewidth=linewidth,
                alpha=alpha
            )

    vspans = kwa.get('vspan', None)

    if vspans is not None:
        color = color_set[0]
        alpha = 0.2
        for vspan in vspans:

            if 'color' in vspan:
                color = vspan['color']

            if 'alpha' in vspan:
                alpha = vspan['alpha']

            plot_vspan(
                axis=ax, index=vspan['ix'],
                color=color, alpha=alpha
            )


def set_axis_label(axis, x=None, y=None, z=None, title=None):

    # Set label
    if x is not None:
        axis.set_xlabel(x)
    if y is not None:
        axis.set_ylabel(y)
    if z is not None:
        axis.set_zlabel(z)
    if title is not None:
        axis.set_title(title)


def _decoration(kwa, ax, legend):
    # Names, title, labels
    ax.locator_params(axis='x', tight=False)

    name = kwa.get('name', None)
    if name is not None:
        ax.text(
            0.5, 0.95, s=name, color=label_colors,
            horizontalalignment='center',
            fontsize=10, transform=ax.transAxes,
            zorder=120
        )

    set_axis_label(
        axis=ax,
        x=kwa.get('xlabel', None),
        y=kwa.get('ylabel', None),
        z=kwa.get('zlabel', None),
        title=kwa.get('title', None)
    )

    main_spine = kwa.get('main_spine', 'left')
    fancy_design(ax, legend, main_spine=main_spine)

    rotation = kwa.get('xtickrotation', 35)
    plt.setp(ax.get_xticklabels(), rotation=rotation)

    if kwa.get('disable_x_ticks', False):
        # Deactivates labels always for all shared axes
        labels = [
            item.get_text()
            for item in ax.get_xticklabels()
        ]
        ax.set_xticklabels([''] * len(labels))

    # ax.autoscale(True)


def xhline(kwa, ax):

    xhline_red = kwa.get('xhline_red', None)
    if xhline_red is not None:
        ax.axhline(xhline_red, color=red,
                   linewidth=0.5)

    xhline_green = kwa.get('xhline_green', None)
    if xhline_green is not None:
        ax.axhline(xhline_green, color=green,
                   linewidth=0.5)

    xhlines = kwa.get('xhline', None)

    if xhlines is not None:
        linewidth = 0.5
        linestyle = None
        color = accent_color

        for line in xhlines:

            if 'color' in line:
                color = line['color']

            if 'linewidth' in line:
                linewidth = line['linewidth']

            if 'linestyle' in line:
                linestyle = line['linestyle']

            ax.axhline(
                line['ix'],
                color=color,
                linewidth=linewidth,
                linestyle=linestyle
            )


def _save_or_show(kwa, fig):
    save = kwa.get('save', '')
    if save:
        plt.savefig(save, facecolor=fig.get_facecolor())

    if kwa.get('axis', None) is None and \
            kwa.get('show', True):
        plt.show()


def _plot(fig, ax, kwa, legend=True, data=None, plot_columns=None):

    if plot_columns is None and data is not None:
        plot_columns = list(data)

    # Plot columns
    enable_flags = kwa.get('enable_flags', True)
    gradient_fill = kwa.get('gradient_fill', False)

    if kwa.get('set_flags_at_the_end', True) \
            and data is not None:
        last_index = data.index.values[-1]
    else:
        last_index = None

    if plot_columns is not None and data is not None:
        avaiable_columns = list(data)
        for i, col in enumerate(plot_columns):
            if col in avaiable_columns:
                color = color_set[i % len(color_set)]
                series = data[col]

                line, = ax.plot(series, linewidth=0.7, color=color)

                if gradient_fill:
                    # From https://stackoverflow.com/questions/29321835/is-it-possible-to-get-color-gradients-
                    #           under-curve-in-matplotlib?answertab=votes#tab-top
                    series.dropna(inplace=True)
                    x = series.index
                    y = series.values

                    zorder = line.get_zorder()
                    alpha = line.get_alpha()
                    alpha = 1.0 if alpha is None else alpha

                    z = np.empty((100, 1, 4), dtype=float)
                    rgb = mcolors.colorConverter.to_rgb(color)
                    z[:, :, :3] = rgb
                    z[:, :, -1] = np.linspace(0, alpha, 100)[:, None]

                    xmin, xmax, ymin, ymax = x.min(), x.max(), y.min(), y.max()
                    im = ax.imshow(z, aspect='auto', extent=[xmin, xmax, ymin, ymax],
                                   origin='lower', zorder=zorder)

                    xy = np.column_stack([x, y])
                    xy = np.vstack([[xmin, ymin], xy, [xmax, ymin], [xmin, ymin]])
                    clip_path = Polygon(xy, facecolor='none', edgecolor='none', closed=True)
                    ax.add_patch(clip_path)
                    im.set_clip_path(clip_path)

                if enable_flags:
                    add_price_flag(
                        fig=fig, axis=ax,
                        series=data[col],
                        color=color,
                        last_index=last_index
                    )
            else:
                logger.warning('Column ' + str(col) +
                               ' not found in dataset')

    _decoration(kwa, ax, legend)
    _vspan(kwa, ax)
    xhline(kwa, ax)
    _save_or_show(kwa, fig)

    return fig, ax


def _head(kwargs, data=None, convert_to_numeric=False):

    if kwargs.get('reset_index', False) or kwargs.get('gradient_fill', False):
        data = data.reset_index()
        if 'Date' in list(data):
            data.drop(['Date'], axis=1, inplace=True)

    # Prepare data ------------------------------------------
    if data is not None:
        if not isinstance(data, pd.DataFrame):
            raise ValueError('Data must be a pandas DataFrame')

        if data.empty:
            raise ValueError('DataFrame is empty')

        if convert_to_numeric:
            for col in list(data):
                data[col] = pd.to_numeric(
                    data[col], errors='coerce')

    # Build ax ----------------------------------------------
    fig = kwargs.get('fig', None)
    if fig is None:
        fig, _ = plt.subplots(facecolor=background_color)

    ax = kwargs.get('axis', None)
    if ax is None:
        ax = plt.subplot2grid(
            (4, 4), (0, 0),
            rowspan=4, colspan=4,
            facecolor=background_color
        )
    return data, fig, ax


def _scatter(fig, ax, kwa, legend=True, data=None):
    _vspan(kwa, ax)
    _decoration(kwa, ax, legend)

    # Scatter
    color = kwa.get('color', accent_color)

    ax.scatter(*zip(*data), color=color)

    xhline(kwa, ax)
    _save_or_show(kwa, fig)

    return fig, ax


def _signal_eval(ax, signals, kwargs):
    """
    Plots the signals
    :param ax: Axis
    :param signals: List of patterns with structure:
        [ ..., ['signal', index, price], ...], where
        signal can be either 'BUY' or 'SELL'
    :param kwargs:
        'draw_verticals': Plots vertical lines
            for each BUY and SELL
        'signl_evaluation': Plot signals
        'signl_evaluation_form': 'rectangles' or
            'arrows_1'
        'dots': Plot dots at 'BUY' and 'SELL' points
    :return:
    """
    if signals is not None:
        if kwargs.get('draw_verticals', True):
            draw_verticals(axis=ax, signals=signals)
        if kwargs.get('signal_evaluation', True):
            draw_signal_evaluation(
                axis=ax,
                signals=signals,
                eval_type=kwargs.get(
                    'signal_evaluation_form',
                    'rectangle'),
                dots=kwargs.get('dots', True),
                red=label_colors,
                green=accent_color,
                disable_red_signals=kwargs.get(
                    'disable_red_signals', False),
                disable_green_signals=kwargs.get(
                    'disable_green_signals', False)
            )


def _pattern_eval(data, ax, cs_patterns, kwargs):
    """
    Plots the candlestick patterns
    :param data: Data
    :param ax: Axis
    :param cs_patterns: List of patterns with structure:
        [ ..., ['pattern_name', start_index,
            stop_index], ...]
    :param kwargs:
        cs_pattern_evaluation: Enable plotting
        bearish_filter: List of strings. If one of the
            strings matches the string or sub string of
            the pattern name the pattern will be visualised
            in red.
        bullish_filter: List of strings. If one of the
            strings matches the string or sub string of
            the pattern name the pattern will be visualised
            in green.
    :return:
    """
    if cs_patterns is not None:
        if kwargs.get('cs_pattern_evaluation', True):
            df = data[['open', 'high', 'low', 'close']]
            draw_pattern_evaluation(
                axis=ax,
                data_ohlc=df,
                cs_patterns=cs_patterns,
                red=label_colors,
                green=accent_color,
                bearish_filter=kwargs.get('bearish_filter', ['be']),
                bullish_filter=kwargs.get('bullish_filter', ['bu']),
            )


def fancy_design(axis, legend=True, main_spine='left'):
    """
    This function changes the design for
        - the legend
        - spines
        - ticks
        - grid
    :param axis: Axis
    :param legend: Legend
    :param main_spine: Visible spine
        can be left, right, top, bottom
    """
    if legend:
        legend = axis.legend(
            loc='best', fancybox=True, framealpha=0.3
        )

        legend.get_frame().set_facecolor(background_color)
        legend.get_frame().set_edgecolor(label_colors)

        for line, text in zip(legend.get_lines(),
                              legend.get_texts()):
            text.set_color(line.get_color())

    axis.grid(linestyle='dotted', color=label_colors, alpha=0.7, animated=True)

    axis.yaxis.label.set_color(label_colors)
    axis.xaxis.label.set_color(label_colors)
    axis.yaxis.label.set_color(label_colors)

    for spine in axis.spines:
        if spine == main_spine:
            axis.spines[spine].set_color(label_colors)
        else:
            axis.spines[spine].set_color(background_color)

    axis.tick_params(
        axis='y', colors=label_colors,
        which='major', labelsize=10,
        direction='in', length=2,
        width=1
    )

    axis.tick_params(
        axis='x', colors=label_colors,
        which='major', labelsize=10,
        direction='in', length=2,
        width=1
    )


def add_price_flag(fig, axis, series, color, last_index=None):
    """
    Add a price flag at the end of the data
    series in the chart
    :param fig: Figure
    :param axis: Axis
    :param series: Pandas Series
    :param color: Color of the flag
    :param last_index: Last index
    """

    series = series.dropna()
    value = series.tail(1)

    try:
        index = value.index.tolist()[0]
        if last_index is not None:
            axis.plot(
                [index, last_index], [value.values[0], value.values[0]],
                color=color, linewidth=0.6, linestyle='--', alpha=0.6
            )
        else:
            last_index = index

        trans_offset = mtrans.offset_copy(
            axis.transData, fig=fig,
            x=0.05, y=0.0, units='inches'
        )

        # Add price text box for candlestick
        x = value.values[0]
        if isinstance(x, float):
            x = format(x, '.6f')

        axis.text(
            last_index, value.values, x,
            size=7, va="center", ha="left",
            transform=trans_offset,
            color='white',
            bbox=dict(
                boxstyle="angled,pad=0.2",
                alpha=0.6, color=color
            )
        )

    except IndexError:
        pass


def plot_candlestick(
        data, signals=None, cs_patterns=None,
        plot_columns=None, **kwargs):
    """
    This function plots a candlestick chart
    :param data: Pandas DataFrame
    :param signals: List of signals with structure
        [(signal, index, price), ... ]. Signal can be 'BUY'
        or 'SELL'
    :param cs_patterns: List of candlestick patterns with structure
    patterns = [... , ['pattern_name', start_index, stop_index], ... ]
    :param plot_columns: List of columns in the given DataFrame like
        plot_columns=['bband_upper_20', 'bband_lower_20']
    :param kwargs:
        'fig': Figure.
        'axis': Axis. If axis is not given the chart will
            plt.plot automatically
        'name': Name of the chart
        'draw_verticals': plots vertical lines for each BUY and SELL
        'signl_evaluation': plot signals
        'signl_evaluation_form': 'rectangles' or 'arrows_1'
        'disable_red_signals': Disables red signals if True
        'disable_green_signals': Disables red signals if True
        'cs_pattern_evaluation': plot candlestick pattern
        'dots': Plot dots at 'BUY' and 'SELL' points
        'enable_flags': Enable flags
        'set_flags_at_the_end': Set flags at the end of the chart
        'xhline': list of dictionaries like:
            xhline= [
                {'ix': 0.1, 'color': 'red'},
                {'ix': -0.1, 'linestyle': '--'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
        'xhline_red': Red horizontal line
        'xhline_green': Green horizontal line
        'vline': List of dictionaries like:
            [
                {'ix': 1},
                {'ix': 2, 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
                alpha: Alpha
        'vspan': List of dictionaries like:
            [
                {'ix': (1, 2)},
                {'ix': (3, 4), 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                alpha: Alpha
        'xtickrotation': Angle of the x ticks
        'xlabel': x label
        'ylabel': y label
        'gradient_fill': If True color gradients are activated
        'title': title
        'disable_x_ticks': Disables the x ticks
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """
    data, fig, ax = _head(kwargs=kwargs, data=data)

    # Add candlestick
    _candlestick2_ohlc(
        ax,
        data['open'], data['high'],
        data['low'], data['close'],
        width=0.6,
        colorup=accent_color,
        colordown=label_colors,
        alpha=1
    )

    _signal_eval(ax, signals, kwargs)
    _pattern_eval(data, ax, cs_patterns, kwargs)

    return _plot(
        fig=fig,
        ax=ax,
        kwa=kwargs,
        data=data,
        plot_columns=plot_columns
    )


def plot_filled_ohlc(
        data, signals=None, cs_patterns=None,
        plot_columns=None, **kwargs):
    """
    This function plots a filled ohlc line chart
    :param data: Pandas DataFrame
    :param signals: List of signals with structure
        [(signal, index, price), ... ]. Signal can be 'BUY'
        or 'SELL'
    :param cs_patterns: List of candlestick patterns with structure
    patterns = [... , ['pattern_name', start_index, stop_index], ... ]
    :param plot_columns: List of columns in the given DataFrame like
        plot_columns=['bband_upper_20', 'bband_lower_20']
    :param kwargs:
        'fig': Figure.
        'axis': Axis. If axis is not given the chart will
            plt.plot automatically
        'name': Name of the chart
        'draw_verticals': plots vertical lines for each BUY and SELL
        'signl_evaluation': plot signals
        'signl_evaluation_form': 'rectangles' or 'arrows_1'
        'disable_red_signals': Disables red signals if True
        'disable_green_signals': Disables red signals if True
        'cs_pattern_evaluation': plot candlestick pattern
        'dots': Plot dots at 'BUY' and 'SELL' points
        'enable_flags': Enable flags
        'set_flags_at_the_end': Set flags at the end of the chart
        'xhline': list of dictionaries like:
            xhline= [
                {'ix': 0.1, 'color': 'red'},
                {'ix': -0.1, 'linestyle': '--'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
        'xhline_red': Red horizontal line
        'xhline_green': Green horizontal line
        'vline': List of dictionaries like:
            [
                {'ix': 1},
                {'ix': 2, 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
                alpha: Alpha
        'vspan': List of dictionaries like:
            [
                {'ix': (1, 2)},
                {'ix': (3, 4), 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                alpha: Alpha
        'xtickrotation': Angle of the x ticks
        'xlabel': x label
        'ylabel': y label
        'gradient_fill': If True color gradients are activated
        'title': title
        'disable_x_ticks': Disables the x ticks
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """
    data, fig, ax = _head(kwargs=kwargs, data=data)

    # Add filled_ohlc
    ax.fill_between(
        data.index,
        data['close'],
        data['high'],
        where=data['close'] <= data['high'],
        facecolor=accent_color,
        interpolate=True,
        alpha=0.35,
        edgecolor=accent_color
    )
    ax.fill_between(
        data.index,
        data['close'],
        data['low'],
        where=data['low'] <= data['close'],
        facecolor=label_colors,
        interpolate=True,
        alpha=0.35,
        edgecolor=label_colors
    )

    _signal_eval(ax, signals, kwargs)
    _pattern_eval(data, ax, cs_patterns, kwargs)

    return _plot(
        fig=fig,
        ax=ax,
        kwa=kwargs,
        data=data,
        plot_columns=plot_columns
    )


def scatter(data, **kwargs):
    """
    This function provides a simple way to plot scattered data
    :param data: List of tuples
    :param kwargs:
        'fig': Figure.
        'axis': If axis is not given the chart will
            plt.plot automatically
        'name': Name of the chart
        'color': Color of the dots
        'xhline': list of dictionaries like:
            xhline= [
                {'ix': 0.1, 'color': 'red'},
                {'ix': -0.1, 'linestyle': '--'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
        'xhline_red': Red horizontal line
        'xhline_green': Green horizontal line
        'vline': List of dictionaries like:
            [
                {'ix': 1},
                {'ix': 2, 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
                alpha: Alpha
        'vspan': List of dictionaries like:
            [
                {'ix': (1, 2)},
                {'ix': (3, 4), 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                alpha: Alpha
        'xlabel': x label
        'ylabel': y label
        'gradient_fill': If True color gradients are activated
        'title': title
        'disable_x_ticks': Disables the x ticks
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """

    data, fig, ax = _head(kwargs=kwargs, data=data, convert_to_numeric=False)

    return _scatter(
        fig=fig,
        ax=ax,
        legend=kwargs.get('legend', True),
        kwa=kwargs,
        data=data,
    )


def scatter_3d(data, class_conditions=None, threshold=0, **kwargs):
    """
        This function provides a simple way to plot scattered data
        :param data: List of tripel. If None a 3D axis will
            be returned. Then you can plot stuff with
            ax.scatter(x, y, z).
        :param class_conditions:
            IMPORTANT: Must be a list of numerical values with length
            of the list of data.
            This list contains a value for each
            triple that classifies it. If the value in the
            list is greater than the parameter threshold the
            dot will be painted in grey (color can be changed
            by setting color_greater_th). If the value is less
            than threshold the dot will be the accent color
            of this library (can be set with color_less_th)
        :param threshold: Threshold of the classification
        :param kwargs:
            'color_less_th': Color of the dots if the value
                in the color_conditions list is less than
                the parameter threshold
            'color_greater_th': Color of the dots if the value
                in the color_conditions list is greater than
                the parameter threshold
            'color': If class_conditions is None the color of
                the dots can be set by color.
            'xlabel': x label
            'ylabel': y label
            'zlabel': z label
            'title': title
            'show': If true the chart will be plt.show()
        :return: None
        """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    set_axis_label(
        axis=ax,
        x=kwargs.get('xlabel', None),
        y=kwargs.get('ylabel', None),
        z=kwargs.get('zlabel', None),
        title=kwargs.get('title', None)
    )

    if data is None:
        return ax

    if class_conditions is None:
        color = kwargs.get('color', label_colors)
        for point in data:
            ax.scatter(point[0], point[1], point[2], color=color)

    else:
        if len(data) != len(class_conditions):
            raise ValueError('Lists of data and color_conditions ' +
                             'have not the same length')

        color_below_th = kwargs.get('color_less_th', label_colors)
        color_over_th = kwargs.get('color_greater_th', accent_color)

        if len(data) > 1:
            for i, point in enumerate(data):
                if class_conditions[i] > threshold:
                    ax.scatter(point[0], point[1], point[2], color=color_over_th)
                else:
                    ax.scatter(point[0], point[1], point[2], color=color_below_th)

    if kwargs.get('show', False):
        plt.show()


def plot(data, plot_columns=None, **kwargs):
    """
    This function provides a simple way to plot time series
    for example data['close'].
    :param data: Pandas DataFrame object
    :param plot_columns: Name of the columns to plot.
        If plot_columns is None all columns well be ploted
    :param kwargs:
        'fig': Figure.
        'axis': Axis. If axis is not given the chart will
            plt.plot automatically
        'name': Name of the chart
        'enable_flags': Enable flags
        'set_flags_at_the_end': Set flags at the end of the chart
        'xhline': list of dictionaries like:
            xhline= [
                {'ix': 0.1, 'color': 'red'},
                {'ix': -0.1, 'linestyle': '--'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
        'xhline_red': Red horizontal line
        'xhline_green': Green horizontal line
        'vline': List of dictionaries like:
            [
                {'ix': 1},
                {'ix': 2, 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                linewidth: Linewidth
                linestyle: Linestyle
                alpha: Alpha
        'vspan': List of dictionaries like:
            [
                {'ix': (1, 2)},
                {'ix': (3, 4), 'color': 'green'}
            ]
            Attributes:
                ix: Index
                color: Color
                alpha: Alpha
        'xlabel': x label
        'ylabel': y label
        'gradient_fill': If True color gradients are activated
        'title': title
        'disable_x_ticks': Disables the x ticks
        'reset_index': Reset the index if True
        'legend': If False legend is disabled
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """

    data, fig, ax = _head(kwargs=kwargs, data=data)

    return _plot(
        fig=fig,
        ax=ax,
        legend=kwargs.get('legend', True),
        kwa=kwargs,
        data=data,
        plot_columns=plot_columns
    )


def bar(data, **kwargs):
    """
    This function provides a simple way to plot a barchart
    from a list.
    :param data: List of the data
        Structure: {'key_1', count of key_1, ... }
    :param kwargs:
        'fig': Figure.
        'axis': Axis. If axis is not given the chart will
            plt.plot automatically
        'name': Name of the chart
        'xlabel': x label
        'ylabel': y label
        'title': Title
        'disable_x_ticks': Disables the x ticks
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """
    # prepare data
    x = dict()
    for candle in data:
        if candle in x:
            x[candle] += 1
        else:
            x[candle] = 1
    objects = list(x.keys())

    y_pos = np.arange(len(objects))
    performance = list()
    for key in x:
        performance.append(x[key])

    # Generate chart
    _, fig, ax = _head(kwargs=kwargs)

    # Plot histogram
    ax.barh(
        y_pos, performance,
        align='center', alpha=0.5,
        color=accent_color
    )

    plt.yticks(y_pos, objects)

    return _plot(
        fig=fig,
        ax=ax,
        kwa=kwargs
    )


def hist(data, **kwargs):
    """
    This function provides a simple way to plot a histogram
    from a list.
    :param data: List of the data
        Structure: ['key_1', count of key_1, ... ]
    :param kwargs:
        'fig': Figure.
        'axis': Axis. If axis is not given the chart will
            plt.plot automatically
        'bins': Bins
        'density': Density
        'threshold': Threshold of the values
        'name': Name of the chart
        'xlabel': x label
        'ylabel': y label
        'title': Title
        'disable_x_ticks': Disables the x ticks
        'show': If true the chart will be plt.show()
        'save': Save the image to a specified path like
            save='path_to_picture.png'
    :return: fig, ax
    """
    # Generate chart
    _, fig, ax = _head(kwargs=kwargs)

    # Plot histogram
    bins = kwargs.get('bins', 10)
    density = kwargs.get('density', None)
    ax.hist(
        data, bins, density=density,
        facecolor=accent_color, alpha=0.75,
        align='mid', histtype='bar',
        rwidth=0.9
    )

    # Plot box
    threshold = kwargs.get('threshold', None)
    if threshold is not None:
        count_pos = 0
        count_neg = 0
        for da in data:
            if da > 0:
                count_pos += 1
            else:
                count_neg += 1

        box_text = '<={}: {} \n>{}: {}'.format(
            threshold, count_neg,
            threshold, count_pos)
        _add_text_box(
            fig=fig, axis=ax, text=box_text,
            x_p=80, y_p=90)

    kwargs['main_spine'] = 'bottom'

    return _plot(
        fig=fig,
        ax=ax,
        kwa=kwargs,
    )


def plot_vline(axis, index, linestyle='--', color=color_set[0],
               linewidth=0.8, alpha=0.8):
    """
    Plots one vertical line
    :param axis: Axis
    :param index: Index
    :param linestyle: Can be '-', '--', '-.', ':'
    :param color: Color
    :param linewidth: Linewidth
    :param alpha: Alpha
    """
    axis.axvline(
        index, color=color,
        linewidth=linewidth, alpha=alpha,
        linestyle=linestyle
    )


def plot_vspan(axis, index, color=color_set[0], alpha=0.2):
    """
    Plots one vertical span
    :param axis: Axis
    :param index: [start index, end index]
    :param color: Color
    :param alpha: Alpha
    :return:
    """
    axis.axvspan(
        index[0], index[1],
        facecolor=color,
        alpha=alpha
    )

name = "mpl_finance_ext"

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")

import logging
logging.getLogger("matplotlib.legend").setLevel(logging.ERROR)
logging.getLogger("matplotlib.backends._backend_tk").setLevel(logging.ERROR)

from .mpl_finance_ext import add_price_flag
from .mpl_finance_ext import background_color
from .mpl_finance_ext import bar
from .mpl_finance_ext import fancy_design
from .mpl_finance_ext import green
from .mpl_finance_ext import hist
from .mpl_finance_ext import scatter_3d
from .mpl_finance_ext import label_colors
from .mpl_finance_ext import plot
from .mpl_finance_ext import plot_candlestick
from .mpl_finance_ext import plot_filled_ohlc
from .mpl_finance_ext import red
from .mpl_finance_ext import color_set
from .mpl_finance_ext import plot_vline
from .mpl_finance_ext import plot_vspan

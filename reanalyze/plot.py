import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FuncFormatter
import pandas as pd
import sys

from pandas import DataFrame

from reanalyze import Column


def _select_biolinum_font():
    preferred_fonts = ["Linux Biolinum O", "Linux Biolinum"]
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for font_name in preferred_fonts:
        if font_name in available_fonts:
            return font_name

    print('Error: neither "Linux Biolinum O" nor "Linux Biolinum" is available.', file=sys.stderr)
    sys.exit(1)

def configure_acmart_style():
    selected_font = _select_biolinum_font()
    plt.rcParams.update(
        {
            "font.size": 10,
            "font.family": [selected_font, "sans-serif"],
        }
    )

def create_scatter_plot(df: DataFrame) -> Figure:
    invocations = sorted(df[Column.INVOCATION.value].unique())
    fig, ax = plt.subplots(figsize=(5, 2.8))

    for invocation in invocations:
        invocation_df = df.loc[df[Column.INVOCATION.value] == invocation].sort_values(
            by=Column.INVOCATION.value
        )
        ax.plot(
            invocation_df[Column.INVOCATION.value],
            invocation_df[Column.VALUE.value],
            linestyle="None",
            marker="o",
            markersize=1,
            alpha=0.25,
            label=f"invocation {invocation}",
        )

    ax.set_title(bench)
    ax.set_xlabel("iteration")
    ax.set_ylabel(f"run time in {unit_label}")
    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if len(invocations) <= 8:
        ax.legend(frameon=False, fontsize=8)

    plt.tight_layout()
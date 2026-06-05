import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FuncFormatter
from pandas import DataFrame

from .rebench import Column


def _select_biolinum_font():
    preferred_fonts = ["Linux Biolinum O", "Linux Biolinum"]
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    for font_name in preferred_fonts:
        if font_name in available_fonts:
            return font_name

    print(
        'Error: neither "Linux Biolinum O" nor "Linux Biolinum" is available.',
        file=sys.stderr,
    )
    sys.exit(1)


def configure_acmart_style():
    selected_font = _select_biolinum_font()
    plt.rcParams.update(
        {
            "font.size": 10,
            "font.family": [selected_font, "sans-serif"],
        }
    )


def create_scatter_plot(
    df: DataFrame,
    x_values: Column,
    y_values: Column,
    group_by: Column,
    x_label: str,
    y_label: str,
    y_label_add_unit: bool,
) -> Figure:
    group_col = sorted(df[group_by.value].unique())
    fig, ax = plt.subplots(figsize=(5, 2.8))

    for group in group_col:
        invocation_df = df.loc[df[group_by.value] == group].sort_values(
            by=group_by.value
        )
        ax.plot(
            invocation_df[x_values.value],
            invocation_df[y_values.value],
            linestyle="None",
            marker="o",
            markersize=1,
            alpha=0.25,
            label=f"invocation {group}",
        )

    ax.set_xlabel(x_label)
    if y_label_add_unit:
        unit_label = sorted(df[Column.UNIT.value].unique())[0]
        ax.set_ylabel(f"{y_label} in {unit_label}")
    else:
        ax.set_ylabel(y_label)

    ax.set_ylim(bottom=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if len(group_col) <= 8:
        ax.legend(frameon=False, fontsize=8)

    plt.tight_layout()
    return fig


def create_boxplot(
    df: DataFrame,
    values: Column,
    category: Column,
    value_axis_label: str,
    orientation: str,
    theme_acmart,
) -> Figure:
    plot_df = df.copy()
    plot_df = plot_df.dropna(subset=[values.value, category.value])

    cat_order = sorted(plot_df[category.value].unique())
    plot_df[category.value] = pd.Categorical(
        plot_df[category.value], categories=cat_order, ordered=True
    )

    fig, ax = plt.subplots(figsize=(5, max(2, int(len(cat_order) * 0.23))))
    plot_df.boxplot(
        column=values.value,
        by=category.value,
        orientation=orientation,
        ax=ax,
        patch_artist=True,
        boxprops={"facecolor": "#729fcf", "edgecolor": "#729fcf"},
        medianprops={"color": "black", "linewidth": 1.25},
        flierprops={"markersize": 2, "alpha": 0.1},
    )

    fig.suptitle("")
    ax.set_title("")
    ax.set_xlabel(value_axis_label)
    ax.set_ylabel("")

    if theme_acmart:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(False)

    ax.set_xscale("log")
    ax.set_xlim(0.1, 10)

    tick_formatter = FuncFormatter(lambda x, _: f"{x:g}")
    ax.xaxis.set_major_formatter(tick_formatter)
    ax.xaxis.set_minor_locator(FixedLocator([0.5, 2]))
    ax.xaxis.set_minor_formatter(
        FuncFormatter(lambda x, _: f"{x:g}" if x in (0.5, 2) else "")
    )

    ax.tick_params(axis="x", which="both", length=4, width=1)

    ax.axvline(1, linestyle=":", color="black", linewidth=1)
    ax.invert_yaxis()  # alphabetical, from the top instead of from 0,0

    if theme_acmart:
        plt.tight_layout()

    return fig

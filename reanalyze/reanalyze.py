# pylint: disable=protected-access
from abc import ABC, abstractmethod
from typing import Literal

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from pandas import DataFrame, concat, read_csv

from reanalyze.plot import configure_acmart_style, create_boxplot, create_scatter_plot
from reanalyze.rebench import Column, download_to_cache


class _AnalysisPlan:
    def _subset_to_baseline(self, data_frame: DataFrame) -> DataFrame:
        raise TypeError(f"Not implemented by {type(self).__name__}")

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        raise TypeError(f"Not implemented by {type(self).__name__}")

    def _evaluate_data_operations(self) -> DataFrame:
        raise TypeError(f"Not implemented by {type(self).__name__}")

    def _evaluate_plot_operations(self, data_frame: DataFrame) -> Figure:
        raise TypeError(f"Not implemented by {type(self).__name__}")


class _WithData(ABC):
    @abstractmethod
    def _evaluate_data_operations(self) -> DataFrame:
        raise TypeError(f"Not implemented by {type(self).__name__}")

    def summarize(self) -> str:
        data_frame = self._evaluate_data_operations()

        non_trivial_cols = data_frame.columns[
            data_frame.apply(lambda col: (~col.dropna().isin([0, 1])).any())
        ].tolist()

        non_trivial_cols.remove(Column.EXP_ID.value)
        non_trivial_cols.remove(Column.RUN_ID.value)
        non_trivial_cols.remove(Column.TRIAL_ID.value)
        non_trivial_cols.remove(Column.COMMAND_LINE.value)

        return data_frame[non_trivial_cols].describe(include="all").to_string()

    def stats(self) -> "_StatsWithData":
        return _StatsWithData(self)  # type: ignore


class _StatsWithData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def column(self, column: Column) -> "_StatsForColumn":
        return _StatsForColumn(column, self)

    def _evaluate_data_operations(self) -> DataFrame:
        return self._prev._evaluate_data_operations()


class _StatsForColumn(_AnalysisPlan, _WithData):
    def __init__(self, column: Column, prev: _AnalysisPlan):
        self._column = column
        self._prev = prev

        self._data: DataFrame | None = None

    def latex_macros(self, filename: str) -> "_StatsForColumnLatexMacros":
        return _StatsForColumnLatexMacros(self._column, filename, self)

    def _evaluate_data_operations(self):
        if self._data is None:
            data_frame = self._prev._evaluate_data_operations()
            self._data = data_frame[[self._column.value]]
        return self._data

    def min(self) -> float:
        data_frame = self._evaluate_data_operations()
        return data_frame[self._column.value].min()

    def max(self) -> float:
        data_frame = self._evaluate_data_operations()
        return data_frame[self._column.value].max()

    def median(self) -> float:
        data_frame = self._evaluate_data_operations()
        return data_frame[self._column.value].median()


class _StatsForColumnLatexMacros(_AnalysisPlan, _WithData):
    def __init__(self, column: Column, filename: str, prev: _AnalysisPlan):
        self._column = column
        self._filename = filename
        self._prev = prev

        self._median_macro_name: str | None = None
        self._min_macro_name: str | None = None
        self._max_macro_name: str | None = None

    def median(self, macro_name: str) -> "_StatsForColumnLatexMacros":
        self._median_macro_name = macro_name
        return self

    def min(self, macro_name: str) -> "_StatsForColumnLatexMacros":
        self._min_macro_name = macro_name
        return self

    def max(self, macro_name: str) -> "_StatsForColumnLatexMacros":
        self._max_macro_name = macro_name
        return self

    def _macro(self, name: str, value: float):
        print(f"{name}: {value:.2f}x")
        return f"\\newcommand{{\\{name}}}{{{value:.2f}$\\times$\\xspace}}\n"

    def save_to_string(self) -> str:
        prev: _StatsForColumn = self._prev  # type: ignore
        result = ""
        if self._median_macro_name is not None:
            result += self._macro(self._median_macro_name, prev.median())
        if self._min_macro_name is not None:
            result += self._macro(self._min_macro_name, prev.min())
        if self._max_macro_name is not None:
            result += self._macro(self._max_macro_name, prev.max())

        return result

    def save_macros(self, filename: str):
        result = self.save_to_string()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Saved LaTeX macros to {filename}")


class _ScatterPlotWithNormalizedBaselineData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def save_plot(self, filename: str):
        data_frame = self._prev._evaluate_data_operations()
        data_frame = self._prev._subset_to_experiment(data_frame)
        plot = self._prev._evaluate_plot_operations(data_frame)
        print(f"Saving baseline scatter plot to {filename}")
        plot.savefig(filename)
        plt.close(plot)


class _ScatterPlotWithNormalizedExperimentData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def save_plot(self, filename: str):
        data_frame = self._prev._evaluate_data_operations()
        data_frame = self._prev._subset_to_experiment(data_frame)
        plot = self._prev._evaluate_plot_operations(data_frame)
        print(f"Saving baseline scatter plot to {filename}")
        plot.savefig(filename)
        plt.close(plot)


class _ScatterPlotWithNormalizedData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev
        self._x_values: Column | None = None
        self._y_values: Column | None = None
        self._x_label: str = ""
        self._y_label: str = ""
        self._y_label_add_unit = False
        self._theme_acmart = True
        self._group_by: Column | None = None

    def theme_acmart(self) -> "_ScatterPlotWithNormalizedData":
        self._theme_acmart = True
        return self

    def group_by(self, column: Column) -> "_ScatterPlotWithNormalizedData":
        self._group_by = column
        return self

    def x_values(self, column: Column) -> "_ScatterPlotWithNormalizedData":
        self._x_values = column
        return self

    def y_values(self, column: Column) -> "_ScatterPlotWithNormalizedData":
        self._y_values = column
        return self

    def x_label(self, label: str) -> "_ScatterPlotWithNormalizedData":
        self._x_label = label
        return self

    def y_label(self, label: str) -> "_ScatterPlotWithNormalizedData":
        self._y_label = label
        return self

    def y_label_with_unit(self, label: str) -> "_ScatterPlotWithNormalizedData":
        self._y_label_add_unit = True
        self._y_label = label
        return self

    def baseline(self) -> "_ScatterPlotWithNormalizedBaselineData":
        return _ScatterPlotWithNormalizedBaselineData(self)

    def experiment(self) -> "_ScatterPlotWithNormalizedExperimentData":
        return _ScatterPlotWithNormalizedExperimentData(self)

    def _evaluate_data_operations(self):
        return self._prev._evaluate_data_operations()

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_experiment(data_frame)

    def _evaluate_plot_operations(self, data_frame: DataFrame) -> Figure:
        if self._x_values is None or self._y_values is None or self._group_by is None:
            raise ValueError("x_values, y_values, group_by must be set before plotting")

        # no further plot-related things expected
        assert isinstance(self._prev, _NormalizedBenchmarkData)

        if self._theme_acmart:
            configure_acmart_style()

        return create_scatter_plot(
            data_frame,
            self._x_values,
            self._y_values,
            self._group_by,
            self._x_label,
            self._y_label,
            self._y_label_add_unit,
        )


class _NormalizedExperimentData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def boxplot(self) -> "_BoxPlotWithNormalizedExperimentData":
        return _BoxPlotWithNormalizedExperimentData(self)

    def _evaluate_data_operations(self) -> DataFrame:
        df = self._prev._evaluate_data_operations()
        return self._prev._subset_to_experiment(df)


class _BoxPlotWithNormalizedExperimentData(_AnalysisPlan, _WithData):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev
        self._values: Column | None = None
        self._category: Column | None = None
        self._orientation: Literal["horizontal", "vertical"] = "horizontal"
        self._value_axis_label: str = ""
        self._theme_acmart = True

    def values(self, column: Column) -> "_BoxPlotWithNormalizedExperimentData":
        self._values = column
        return self

    def category(self, column: Column) -> "_BoxPlotWithNormalizedExperimentData":
        self._category = column
        return self

    def value_axis_label(self, label: str) -> "_BoxPlotWithNormalizedExperimentData":
        self._value_axis_label = label
        return self

    def save_plot(self, filename: str):
        if self._values is None or self._category is None:
            raise ValueError("values and category column must be set before plotting")

        data_frame = self._prev._evaluate_data_operations()

        assert isinstance(self._prev, _NormalizedExperimentData)

        if self._theme_acmart:
            configure_acmart_style()

        plot = create_boxplot(
            data_frame,
            self._values,
            self._category,
            self._value_axis_label,
            self._orientation,
            self._theme_acmart,
        )
        print(f"Saving boxplot with experiment data to {filename}")
        plot.savefig(filename)
        plt.close(plot)


class _NormalizedBenchmarkData(_AnalysisPlan, _WithData):
    def __init__(self, benchmark_name: str, prev: _AnalysisPlan):
        self._benchmark_name = benchmark_name
        self._prev = prev

    def scatter_plot(self) -> "_ScatterPlotWithNormalizedData":
        return _ScatterPlotWithNormalizedData(self)

    def _evaluate_data_operations(self) -> DataFrame:
        data_frame = self._prev._evaluate_data_operations()
        return data_frame[data_frame[Column.BENCHMARK.value] == self._benchmark_name]

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_experiment(data_frame)


class _NormalizedData(_AnalysisPlan, _WithData):
    def __init__(self, column: Column, prev: _AnalysisPlan):
        self._column = column
        self._prev = prev

    def benchmark(self, benchmark_name: str) -> "_NormalizedBenchmarkData":
        return _NormalizedBenchmarkData(benchmark_name, self)

    def experiment(self) -> "_NormalizedExperimentData":
        return _NormalizedExperimentData(self)

    def _evaluate_data_operations(self) -> DataFrame:
        data_frame = self._prev._evaluate_data_operations()
        baseline_df = self._prev._subset_to_baseline(data_frame)
        baseline_medians = baseline_df.groupby(self._column.value)[
            Column.VALUE.value
        ].median()
        data_frame[Column.NORMALIZED_VALUE.value] = data_frame.apply(
            lambda row: row[Column.VALUE.value]
            / baseline_medians[row[self._column.value]],
            axis=1,
        )
        return data_frame

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_experiment(data_frame)


class _WithExperimentAndBaselineData(_AnalysisPlan, _WithData):
    def __init__(self, project: str, exp_id: int, prev: _AnalysisPlan):
        self._project = project
        self._exp_id = exp_id
        self._prev = prev

        self._data: DataFrame | None = None

    def normalize_by(self, column: Column) -> _NormalizedData:
        return _NormalizedData(column, self)

    def _evaluate_data_operations(self):
        if self._data is None:
            baseline_df = self._prev._evaluate_data_operations()
            experiment_df = self._load_and_cache_data()
            self._data = concat([baseline_df, experiment_df])
        return self._data

    def _load_and_cache_data(self):
        file_path = download_to_cache(self._exp_id, self._project)
        return read_csv(file_path)

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return data_frame[data_frame[Column.EXP_ID.value] == self._exp_id]

    def _subset_to_baseline(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_baseline(data_frame)


class _WithBaselineData(_AnalysisPlan, _WithData):
    def __init__(self, project: str, exp_id: int, prev: _AnalysisPlan):
        self._project = project
        self._exp_id = exp_id
        self._prev = prev

    def add_experiment_from_db(
        self, project: str, exp_id: int
    ) -> _WithExperimentAndBaselineData:
        return _WithExperimentAndBaselineData(project, exp_id, self)

    def _evaluate_data_operations(self):
        assert isinstance(
            self._prev, ReAnalyze
        )  # `self` should be the first element with data
        baseline_df = self._load_and_cache_data()
        return baseline_df

    def _load_and_cache_data(self):
        file_path = download_to_cache(self._exp_id, self._project)
        return read_csv(file_path)

    def _subset_to_baseline(self, data_frame: DataFrame) -> DataFrame:
        return data_frame[data_frame[Column.EXP_ID.value] == self._exp_id]


class ReAnalyze(_AnalysisPlan):
    def add_baseline_from_db(self, project: str, exp_id: int) -> _WithBaselineData:
        return _WithBaselineData(project, exp_id, self)

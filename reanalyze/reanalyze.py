# pylint: disable=protected-access

from enum import Enum

from pandas import DataFrame, concat, read_csv

from reanalyze.rebench import download_to_cache


class Column(Enum):
    """The columns available in the ReBench data."""

    EXP_ID = "expid"
    RUN_ID = "runid"
    TRIAL_ID = "trialid"
    COMMIT_ID = "commitid"
    BENCHMARK = "bench"
    EXECUTOR = "exe"
    SUITE = "suite"
    COMMAND_LINE = "cmdline"
    VAR_VALUE = "varvalue"
    CORES = "cores"
    INPUT_SIZE = "inputsize"
    EXTRA_ARGS = "extraargs"
    INVOCATION = "invocation"
    WARMUP = "warmup"
    CRITERION = "criterion"
    UNIT = "unit"
    VALUE = "value"
    ITERATION = "iteration"
    ENV_ID = "envid"

    NORMALIZED_VALUE = "normalized_value"


class _AnalysisPlan:
    def _subset_to_baseline(self, data_frame: DataFrame) -> DataFrame:
        raise TypeError()

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        raise TypeError()

    def _evaluate_data_operations(self) -> DataFrame:
        raise TypeError()


class _ScatterPlotWithNormalizedBaselineData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def save_plot(self, filename: str):
        data_frame = self._prev._evaluate_data_operations()
        data_frame = self._prev._subset_to_experiment(data_frame)
        plot = self._prev.evaluate_plot_operations(data_frame)
        print(f"Saving baseline scatter plot to {filename}")
        plot.save(filename)


class _ScatterPlotWithNormalizedExperimentData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev

    def save_plot(self, filename: str):
        data_frame = self._prev._evaluate_data_operations()
        data_frame = self._prev._subset_to_experiment(data_frame)
        plot = self._prev.evaluate_plot_operations(data_frame)
        print(f"Saving baseline scatter plot to {filename}")
        plot.save(filename)


class _ScatterPlotWithNormalizedData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev
        self._x_values: Column | None = None
        self._y_values: Column | None = None
        self._x_label: str = ""
        self._y_label: str = ""
        self._y_label_add_unit = False

    def x_values(self, column: Column) -> _ScatterPlotWithNormalizedData:
        self._x_values = column
        return self

    def y_values(self, column: Column) -> _ScatterPlotWithNormalizedData:
        self._y_values = column
        return self

    def x_label(self, label: str) -> _ScatterPlotWithNormalizedData:
        self._x_label = label
        return self

    def y_label(self, label: str) -> _ScatterPlotWithNormalizedData:
        self._y_label = label
        return self

    def y_label_with_unit(self, label: str) -> _ScatterPlotWithNormalizedData:
        self._y_label_add_unit = True
        self._y_label = label
        return self

    def baseline(self) -> _ScatterPlotWithNormalizedBaselineData:
        return _ScatterPlotWithNormalizedBaselineData(self)

    def experiment(self) -> _ScatterPlotWithNormalizedExperimentData:
        return _ScatterPlotWithNormalizedExperimentData(self)

    def _evaluate_data_operations(self):
        return self._prev._evaluate_data_operations()

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_experiment(data_frame)


class _NormalizedExperimentData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev


class _NormalizedData(_AnalysisPlan):
    def __init__(self, column: Column, prev: _AnalysisPlan):
        self._column = column
        self._prev = prev

    def scatter_plot(self) -> _ScatterPlotWithNormalizedData:
        return _ScatterPlotWithNormalizedData(self)

    def experiment(self) -> _NormalizedExperimentData:
        return _NormalizedExperimentData(self)

    def _evaluate_data_operations(self):
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


class _WithExperimentAndBaselineData(_AnalysisPlan):
    def __init__(self, project: str, exp_id: int, prev: _AnalysisPlan):
        self._project = project
        self._exp_id = exp_id
        self._prev = prev

    def normalize_by(self, column: Column) -> _NormalizedData:
        return _NormalizedData(column, self)

    def _evaluate_data_operations(self):
        baseline_df = self._prev._evaluate_data_operations()
        experiment_df = self._load_and_cache_data()
        return concat([baseline_df, experiment_df])

    def _load_and_cache_data(self):
        file_path = download_to_cache(self._exp_id, self._project)
        return read_csv(file_path)

    def _subset_to_experiment(self, data_frame: DataFrame) -> DataFrame:
        return data_frame[data_frame[Column.EXP_ID.value] == self._exp_id]

    def _subset_to_baseline(self, data_frame: DataFrame) -> DataFrame:
        return self._prev._subset_to_baseline(data_frame)


class _WithBaselineData(_AnalysisPlan):
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

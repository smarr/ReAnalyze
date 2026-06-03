from enum import Enum


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
    pass


class _ScatterPlotWithNormalizedBaselineData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev


class _ScatterPlotWithNormalizedExperimentData(_AnalysisPlan):
    def __init__(self, prev: _AnalysisPlan):
        self._prev = prev


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


class _WithExperimentData(_AnalysisPlan):
    def __init__(self, project: str, run_id: int, prev: _AnalysisPlan):
        self._project = project
        self._run_id = run_id
        self._prev = prev

    def normalize_by(self, column: Column) -> _NormalizedData:
        return _NormalizedData(column, self)


class _WithBaselineData(_AnalysisPlan):
    def __init__(self, project: str, run_id: int, prev: _AnalysisPlan):
        self._project = project
        self._run_id = run_id
        self._prev = prev

    def add_experiment_from_db(self, project: str, run_id: int) -> _WithExperimentData:
        return _WithExperimentData(project, run_id, self)


class ReAnalyze(_AnalysisPlan):
    def add_baseline_from_db(self, project: str, run_id: int) -> _WithBaselineData:
        return _WithBaselineData(project, run_id, self)

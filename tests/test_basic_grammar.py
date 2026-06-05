# pylint: disable=redefined-outer-name
from pytest import fixture

from reanalyze import Column, ReAnalyze


@fixture
def normalized():
    return (
        ReAnalyze()
        .add_baseline_from_db("PlissDemo", 5843)
        .add_experiment_from_db("PlissDemo", 5844)
        .normalize_by(Column.BENCHMARK)
    )


def test_plot_iteration_time(normalized):
    plot_iteration_time = (
        normalized.benchmark("Sieve")
        .scatter_plot()
        .group_by(Column.INVOCATION)
        .x_values(Column.ITERATION)
        .y_values(Column.VALUE)
        .x_label("iteration")
        .y_label_with_unit("run time")
    )
    plot_iteration_time.baseline().save_plot("baseline-iteration-time.pdf")
    plot_iteration_time.experiment().save_plot("experiment-iteration-time.pdf")


def test_plot_change_boxplot(normalized):
    plot_change = (
        normalized.experiment()
        .boxplot()
        .values(Column.NORMALIZED_VALUE)
        .category(Column.BENCHMARK)
        .value_axis_label("run time factor compared to baseline")
    )
    plot_change.save_plot("change-boxplot.pdf")

    # sieve_norm = r.data[Column.BENCHMARK == "Sieve", Column.NORMALIZED_VALUE]
    #
    # with open("results.tex", "w") as f:
    #     write_macro("sieveMedian", sieve_norm.median(), f)
    #     write_macro("sieveMin", sieve_norm.min(), f)
    #     write_macro("sieveMax", sieve_norm.max(), f)

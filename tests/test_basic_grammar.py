# pylint: disable=redefined-outer-name
from os.path import exists

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


# pylint: disable=line-too-long
def test_summarize():
    data = (
        ReAnalyze()
        .add_baseline_from_db("PlissDemo", 5843)
        .add_experiment_from_db("PlissDemo", 5844)
    )
    expected_summary = (
        "       commitid  bench    exe      suite    extraargs    invocation criterion   unit         value     iteration    envid\n"  # noqa: E501
        "count     10000  10000  10000      10000  10000.00000  10000.000000     10000  10000  10000.000000  10000.000000  10000.0\n"  # noqa: E501
        "unique        2      4      1          1          NaN           NaN         1      1           NaN           NaN      NaN\n"  # noqa: E501
        "top      a14ebb  Sieve   java  awfy-java          NaN           NaN     total     ms           NaN           NaN      NaN\n"  # noqa: E501
        "freq       5000   2500  10000      10000          NaN           NaN     10000  10000           NaN           NaN      NaN\n"  # noqa: E501
        "mean        NaN    NaN    NaN        NaN   1400.00000      3.000000       NaN    NaN     63.976215    125.500000      6.0\n"  # noqa: E501
        "std         NaN    NaN    NaN        NaN    938.13006      1.414284       NaN    NaN     32.134178     72.171815      0.0\n"  # noqa: E501
        "min         NaN    NaN    NaN        NaN    600.00000      1.000000       NaN    NaN     34.688000      1.000000      6.0\n"  # noqa: E501
        "25%         NaN    NaN    NaN        NaN    900.00000      2.000000       NaN    NaN     36.517000     63.000000      6.0\n"  # noqa: E501
        "50%         NaN    NaN    NaN        NaN   1000.00000      3.000000       NaN    NaN     53.434500    125.500000      6.0\n"  # noqa: E501
        "75%         NaN    NaN    NaN        NaN   1500.00000      4.000000       NaN    NaN    109.057500    188.000000      6.0\n"  # noqa: E501
        "max         NaN    NaN    NaN        NaN   3000.00000      5.000000       NaN    NaN    232.480000    250.000000      6.0"  # noqa: E501
    )
    assert data.summarize() == expected_summary


# pylint: enable=line-too-long


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


def test_latex(normalized):
    stats = (
        normalized.benchmark("Sieve")
        .stats()
        .column(Column.NORMALIZED_VALUE)
        .latex_macros("results.tex")
        .median("sieveMedian")
        .min("sieveMin")
        .max("sieveMax")
    )
    stats.save_macros("results.tex")

    result = stats.save_to_string()
    assert result == (
        "\\newcommand{\\sieveMedian}{0.9701970124104857}\n"
        "\\newcommand{\\sieveMin}{0.5852208288778717}\n"
        "\\newcommand{\\sieveMax}{1.786008230452675}\n"
    )

    # assert that results.tex exists
    assert exists("results.tex")

    # assert that results.tex contains the expected macros

    with open("results.tex", "r", encoding="utf-8") as f:
        content = f.read()
        assert content == result

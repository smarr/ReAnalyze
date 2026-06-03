from reanalyze import Column, ReAnalyze


def test_basic_scenario():
    r = (
        ReAnalyze()
        .add_baseline_from_db("PlissDemo", 5843)
        .add_experiment_from_db("PlissDemo", 5844)
        .normalize_by(Column.BENCHMARK)
    )

    plot_change = (
        r.scatter_plot()
        .x_values(Column.ITERATION)
        .y_values(Column.VALUE)
        .x_label("iteration")
        .y_label_with_unit("run time")
    )
    plot_change.baseline().save("baseline-iteration-time.pdf")
    plot_change.experiment().save("experiment-iteration-time.pdf")

    plot_iteration_time = (
        r.experiment()
        .boxplot()
        .x_values(Column.NORMALIZED_VALUE)
        .y_values(Column.BENCHMARK)
        .x_label("run time factor compared to baseline")
    )
    plot_iteration_time.save("change-boxplot.pdf")

    sieve_norm = r.data[Column.BENCHMARK == "Sieve", Column.NORMALIZED_VALUE]

    with open("results.tex", "w") as f:
        write_macro("sieveMedian", sieve_norm.median(), f)
        write_macro("sieveMin", sieve_norm.min(), f)
        write_macro("sieveMax", sieve_norm.max(), f)

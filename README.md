# ReAnalyze: Grammar of Benchmark Analyses and Graphics

This project is inspired by the notion of Grammar of Graphics and ggplot2,
which provides a Layered Grammar of Graphics.

Currently, this is merely an exploration, of what a Grammar of Benchmark
Analyses could look like.

The eventual goal would be to provide a library that encapsulates a set of
common tasks for the analysis of performance measurements. Specifically, we are
working in the field of programming language implementation, compilation,
garbage collection, and similar, which will also guide which types of analyses
we are interested in.

This may look like this:

```Python
normalized = (
  ReAnalyze()
  .add_baseline_from_db("PlissDemo", 5843)
  .add_experiment_from_db("PlissDemo", 5844)
  .normalize_by(Column.BENCHMARK)
)

normalized.benchmark("Sieve")
  .scatter_plot()
  .group_by(Column.INVOCATION)
  .x_values(Column.ITERATION)
  .y_values(Column.VALUE)
  .x_label("iteration")
  .y_label_with_unit("run time")
  .experiment()
  .save_plot("experiment-iteration-time.pdf")
```

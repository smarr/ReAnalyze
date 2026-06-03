python3.14 -m black reanalyze tests
python3.14 -m isort reanalyze tests
python3.14 -m pylint reanalyze tests
python3.14 -m flake8 reanalyze tests
python3.14 -m mypy reanalyze tests
#python3.14 -m bandit -r reanalyze/tests
#python3.14 -m safety check --full-report
#python3.14 -m vulture reanalyze/tests --min-confidence 100
#python3.14 -m pytype reanalyze/tests
#python3.14 -m pyflakes reanalyze/tests
#python3.14 -m pydocstyle reanalyze/tests

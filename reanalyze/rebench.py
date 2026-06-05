import gzip
import sys
from enum import Enum
from os import makedirs
from os.path import basename, exists, join
from time import sleep
from urllib.error import HTTPError
from urllib.request import urlretrieve


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


def _file_name(data_id):
    return f"{data_id}.csv.gz"


def _data_url(data_id, project_name):
    return f"https://rebench.dev/{project_name}/data/{_file_name(data_id)}"


def is_valid_gzip(path: str) -> bool:
    try:
        with gzip.open(path, "rb") as f:
            # Read a bit to force decompression and CRC/header checks.
            while f.read(1024 * 1024):
                pass
        return True
    except OSError:
        return False


def download_to_cache(exp_id: int, project_name: str, cache_dir: str = "cache") -> str:
    makedirs(cache_dir, exist_ok=True)

    file_name = basename(_file_name(exp_id))
    if not file_name:
        raise ValueError(f"Could not determine file name from {file_name}")

    target_path = join(cache_dir, file_name)
    url = _data_url(exp_id, project_name)
    if exists(target_path) and is_valid_gzip(target_path):
        return target_path

    try:
        print(f"Downloading {url} -> {target_path}")
        urlretrieve(url, target_path)

        retry = 3
        while retry > 0:
            if is_valid_gzip(target_path):
                break

            print(
                f"File {target_path} is not a valid gzip file. Retrying... in 10 sec."
            )
            try:
                urlretrieve(url, target_path)
            except HTTPError as e:
                print(f"Download failed: {e}")
            retry -= 1
            sleep(10)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to download {url}: {e}")
        sys.exit(1)

    return target_path

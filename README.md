# opentelemetry-auto-instr-python
The auto-instrumentation for Python (per [OTEP 0001](https://github.com/open-telemetry/oteps/blob/master/text/0001-telemetry-without-manual-instrumentation.md)) instruments each library in a separately installable package to ensure users only need to install the libraries that make sense for their use-case. This repository contains the code initially [donated by DataDog](https://www.datadoghq.com/blog/opentelemetry-instrumentation/) in the `reference` folder. All instrumentation that has been ported lives in the `instrumentation` directory.

# porting ddtrace/contrib to instrumentation

The steps below describe the process to port integrations from the reference directory containing the originally donated code to OpenTelemetry.

1. Move the code into the instrumentation directory

```
mkdir -p instrumentation/opentelemetry-instrumentation-jinja2/src/opentelemetry/instrumentation/jinja2
git mv reference/ddtrace/contrib/jinja2 instrumentation/opentelemetry-instrumentation-jinja2/src/opentelemetry/instrumentation/jinja2
```

2. Move the tests

```
git mv reference/tests/contrib/jinja2 instrumentation/opentelemetry-instrumentation-jinja2/tests
```

3. Add `README.rst`, `setup.cfg` and `setup.py` files and update them accordingly

```bash
cp _template/* instrumentation/opentelemetry-instrumentation-jinja2/
```

4. Add `version.py` file and update it accordingly

```bash
mv instrumentation/opentelemetry-instrumentation-jinja2/version.py instrumentation/opentelemetry-instrumentation-jinja2/src/opentelemetry/instrumentation/jinja2/version.py
```

5. Fix relative import paths to using ddtrace package instead of using relative paths
6. Update the code and tests to use the OpenTelemetry API

# Running Tests

1. Create a virtual env in your Contrib repo directory. `python3 -m venv my_test_venv`.
2. Activate your virtual env. `source my_test_env/bin/activate`.
3. Clone the [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python) Python Core repo to a folder named `opentelemetry-python-core`. `git clone git@github.com:open-telemetry/opentelemetry-python.git opentelemetry-python-core`.
4. Change directory to the repo that was just cloned. `cd opentelemetry-python`.
5. Move the head of this repo to the hash you want your tests to use. This is currently `51ed4576c611316bd3f74d213501f5ffa3e2a5ca` as seen in `.github/workflows/test.yml`. Use `git checkout 51ed4576c611316bd3f74d213501f5ffa3e2a5ca`.
6. Go back to the root directory. `cd ../`.
7. Make sure you have `tox` installed. `pip install tox`.
8. Run tests for a package. (e.g. `tox -e test-instrumentation-flask`.)

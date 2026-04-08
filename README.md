# zuul-sphinx-intersphinx-test

A test environment for validating intersphinx and zuul-sphinx behavior

This test uses nox (and will use uv internally).

## Setup:

### Install requirements

The following programs must be installed and in the path in order to execute
these tests conveniently.

* `nox`

## Running the test environment

### Run the documentation

```bash
nox -s docs
```

This will autobuild the documentation against the sphinx documentation.

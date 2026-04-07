# zuul-sphinx-intersphinx-test

A test environment for validating intersphinx and zuul-sphinx behavior

This test uses nox (and will use uv internally).

## Setup:

### Install requirements

The following programs must be installed and in the path in order to execute
these tests conveniently.

* `docker` with the `compose` plugin (either docker engine or docker desktop will work for this example)
    * [Docker CE instructions](https://docs.docker.com/engine/install/#installation-procedures-for-supported-platforms)
    * [Docker Desktop](https://docs.docker.com/get-started/get-docker/)
* `nox`

### Grab zuul sphinx source code

Clone zuul-sphinx to `remote-sphinx-server/zuul-sphinx/`

```bash
cd remote-sphinx-server
git clone https://opendev.org/zuul/zuul-sphinx.git zuul-sphinx
```

### Apply this patch to the git repository:

```bash
git fetch https://review.opendev.org/zuul/zuul-sphinx refs/changes/25/982925/1 && git cherry-pick FETCH_HEAD
```

## Running the test environment

### Run the auto-doc server

```bash
nox -s doc-server
```

This will form the following steps:

1. Rebuild the zuul-sphinx documentation in that repository
2. Launch a docker based webserver that will host the zuul-sphinx project
documentation on http://localhost:7999
3. Run sphinx-autobuild on this repository to dynamically refresh the sphinx
   documentation until user interrupts the process. (hosted on port http://localhost:7999)
4. Cleanup (tears down the docker server.)


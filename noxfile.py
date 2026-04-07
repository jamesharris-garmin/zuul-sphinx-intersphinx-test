"""Example build jobs for intersphinx

This nox file is used to run sphinx-build to validate sphinx configurations.
"""

import shutil
from itertools import chain, repeat
from pathlib import Path

import nox

PROJECT_ROOT = Path(__file__).parent

SPHINX_DIR = PROJECT_ROOT / "docs"
"The Sphinx root dir"

SPHINX_SRC_DIR = SPHINX_DIR
"The Sphinx source directory"

SPHINX_OUTPUT_DIR = SPHINX_DIR / "_build"
"The Sphinx output directory"

ZUUL_SPHINX_DIR = PROJECT_ROOT / "remote-sphinx-server" / "zuul-sphinx"
"The path to the zuul-sphinx clone"


# disable automatic session running.
nox.options.sessions = ["docs"]

# Prefer UV for speed.
nox.options.default_venv_backend = "uv|venv"

# this VENV_DIR constant specifies the name of the dir that the `dev`
# session will create, containing the virtualenv;
# the `resolve()` makes it portable
VENV_DIR = (PROJECT_ROOT / ".venv").resolve()


def install_uv_project(
    session: nox.Session,
    extras=None,
    groups=None,
    only_groups=None,
    no_groups=None,
    use_pip_interface=False,
):
    """Export the uv requirements to something pip understands.

    This patch invokes uv export to export the lockfile contents to the

    :param session: the current nox session.
    :type session: nox.Session
    """

    uv_external = True
    if session.venv_backend != "uv":
        session.install("uv>=0.5.1")
        uv_external = False

    uv_cmd = uv_sync_cmd = [
        "uv",
        "sync",
        "--quiet",
        "--frozen",
        "--inexact",
    ]

    uv_export_cmd = [
        "uv",
        "export",
        "--quiet",
        "--frozen",
    ]

    if use_pip_interface:
        uv_cmd = uv_export_cmd

    def _transform_list_to_arg(flag, input):
        """Convert a list of inputs or single string input into a list of

        ['--flag', input[0], ..., '--flag', input[n]]

        for repeating arguments to the commandline.

        :param flag: the cli flag to add in front of every element
        :type flag: str
        :param input: a list of elements or single string to convert.
        :type input: string or list
        """

        def _as_list(str_or_list=None):
            if isinstance(str_or_list, str):
                return [str_or_list]

            return str_or_list

        if isinstance(input_list := _as_list(input), list):
            return chain.from_iterable(zip(repeat(flag), input_list))

        return None

    if group_arg_list := _transform_list_to_arg("--group", groups):
        uv_cmd.extend(group_arg_list)

    if no_group_arg_list := _transform_list_to_arg("--no-group", no_groups):
        uv_cmd.extend(no_group_arg_list)

    if only_group_arg_list := _transform_list_to_arg("--only-group", only_groups):
        uv_cmd.extend(only_group_arg_list)

    if extras == "all" and not only_groups:
        uv_cmd.append("--all-extras")
    elif extras_arg_list := _transform_list_to_arg("--extra", extras):
        uv_cmd.extend(extras_arg_list)

    session.env["UV_PROJECT_ENVIRONMENT"] = session.virtualenv.location

    if session.python:
        session.env["UV_PYTHON"] = str(session.python)

    if use_pip_interface:
        req_dir = Path(session.create_tmp())
        req_file = req_dir / "requirements.txt"
        uv_cmd.extend(
            [
                "--directory",
                str(req_dir.resolve()),
                "--output-file",
                str(req_file.resolve()),
            ],
        )
        session.run_install(*uv_cmd)
        session.install("-r", str(req_file.resolve()))
        shutil.rmtree(req_dir)
    else:
        session.run_install(
            *uv_sync_cmd,
            external=uv_external,
        )


@nox.session(reuse_venv=True)
def zuul_sphinx_docs(session: nox.Session):
    "build zuul_sphinx documentation."
    session.install("nox")
    with session.chdir(ZUUL_SPHINX_DIR):
        session.run("nox", "-s", "docs", "-fb", "uv")


@nox.session(venv_backend=None)
def start_docker_compose(session: nox.Session):
    "start the zuul-sphinx webserver in the background"
    session.run("docker", "compose", "up", "-d", external=True)


@nox.session(venv_backend=None)
def stop_docker_compose(session: nox.Session):
    "build zuul_sphinx documentation."
    session.run("docker", "compose", "down", external=True)


@nox.session(requires=["zuul_sphinx_docs", "start_docker_compose"])
def docs(session: nox.Session):
    "Build sphinx documentation with case"

    install_uv_project(session)

    output_dir = SPHINX_OUTPUT_DIR

    html_dir = output_dir / "_html"
    doctree_dir = output_dir / "_doctree"

    start_docker_compose(session)

    try:
        session.run(
            "sphinx-build",
            "-E",
            "-W",
            # "-vvvv",
            "-d",
            str(doctree_dir.relative_to(PROJECT_ROOT)),
            "-b",
            "html",
            str(SPHINX_SRC_DIR.relative_to(PROJECT_ROOT)),
            str(html_dir.relative_to(PROJECT_ROOT)),
        )
    finally:
        session.notify("stop_docker_compose")


@nox.session(name="doc-server", requires=["zuul_sphinx_docs", "start_docker_compose"])
def doc_server(session: nox.Session):
    "launch sphinx autobuild server"

    install_uv_project(session)

    output_dir = SPHINX_OUTPUT_DIR

    html_dir = output_dir / "_html"

    start_docker_compose(session)

    try:
        session.run(
            "sphinx-autobuild",
            "-a",
            "-E",
            str(SPHINX_SRC_DIR.relative_to(PROJECT_ROOT)),
            str(html_dir.relative_to(PROJECT_ROOT)),
        )
    finally:
        session.notify("stop_docker_compose")

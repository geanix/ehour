#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `ehour` package."""

import pytest

from click.testing import CliRunner

from ehour import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_cli():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.cli)
    assert result.exit_code == 0
    assert 'CLI interface for eHour 2' in result.output
    help_result = runner.invoke(cli.cli, ['--help'])
    assert help_result.exit_code == 0
    assert 'Usage: ehour [OPTIONS] COMMAND' in help_result.output


def test_cli_clients():
    """Test the CLI clients command."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ['-k', 'FOOBAR', 'clients', '--help'])
    print(result.output)
    assert result.exit_code == 0
    assert 'Usage: ehour clients' in result.output

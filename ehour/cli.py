# -*- coding: utf-8 -*-

"""Console script for ehour."""
import sys
import click
import json

import ehour.api


@click.group(name='ehour')
@click.option('--api-key', '-k', envvar='EHOUR_API_KEY',
              type=str, required=True,
              help='API key for eHour API '
              '(defaults to $EHOUR_API_KEY environment variable)')
@click.option('--config-file', '-c', envvar='EHOUR_CONFIG_FILE',
              type=click.File('r'))
@click.pass_context
def cli(ctx, api_key, config_file):
    """CLI interface for eHour 2.

    This commands enables shell access to eHour 2 data using the REST API.
    eHour 2 is a cloud hosted timesheet management solution. See
    https://getehour.com for details.
    """
    ctx.obj = {
        'api-key': api_key,
        'config-file': config_file,
    }


def connect(api_key, config_file):
    api = ehour.api.API
    api.connect(key=api_key, config_file=config_file)
    return api


@cli.command()
@click.option('--json', '-j', 'json_output', is_flag=True,
              help='Output as JSON (default is simple human readable).')
@click.option('--verbose', '-v', count=True,
              help='Verbose output.')
@click.option('--id', 'client_id', type=str, multiple=True,
              help='Filter on client ID.')
@click.option('--code', type=str, multiple=True,
              help='Filter on client code field.')
@click.pass_context
def clients(ctx, json_output, verbose, client_id, code):
    """Show list of clients."""
    ehour = connect(ctx.obj['api-key'], ctx.obj['config-file'])
    clients = ehour.clients()
    if client_id:
        clients = [c for c in clients if c.id in client_id]
    if code:
        clients = [c for c in clients if c.code in code]
    # Client IDs is an integer prefixed with 'CLT', so let's sort list based
    # on the id integer value
    clients.sort(key=lambda c: int(c.id[3:]))
    print_list_of_elements_with_code_and_name(clients, json_output, verbose)


@cli.command()
@click.option('--client', type=str,
              help='List only projects for client (id).')
@click.option('--inactive', is_flag=True,
              help='Include inactive projects.')
@click.option('--json', '-j', 'json_output', is_flag=True,
              help='Output as JSON (default is simple human readable).')
@click.option('--verbose', '-v', count=True,
              help='Verbose output.')
@click.pass_context
def projects(ctx, client, inactive, json_output, verbose):
    """Show list of projects.

    Use --client to show only projects for a given client (can be used
    multiple times for a combined list of projects for more clients).
    """
    ehour = connect(ctx.obj['api-key'], ctx.obj['config-file'])
    if client:
        client = ehour.client(client)
        projects = ehour.projects_for_client(client, only_active=not inactive)
    else:
        projects = ehour.projects(only_active=not inactive)
    print_list_of_elements_with_code_and_name(projects, json_output, verbose)


def print_list_of_elements_with_code_and_name(elements, json_output, verbose):
    if not json_output and verbose == 0:
        for e in elements:
            print(f'{e.id}: {e.name} [{e.code}]')
        return
    elements = [vars(e) for e in elements]
    if verbose == 0:
        fields = ('id', 'code', 'name')
        elements = [{k: v for k, v in e.items() if k in fields}
                    for e in elements]
    if json_output:
        print(json.dumps(elements))
        return
    # Verbose human readable output
    for e in elements:
        for k, v in e.items():
            if v is None:
                continue
            elif isinstance(v, list):
                print(f'{k}:\n    ' + '\n    '.join(v))
            elif type(v) not in (str, int, bool):
                continue
            else:
                print(f'{k}: {v}')
        print()


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover

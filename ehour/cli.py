# -*- coding: utf-8 -*-

"""Console script for ehour."""
import sys
import click
import json

from ehour.api import EhourApi


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
    ctx.obj = EhourApi(key=api_key, config_file=config_file)


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
    ehour = ctx.obj
    clients = ehour.clients(fill=verbose > 0)
    if client_id:
        clients = [c for c in clients if c.id in client_id]
    if code:
        clients = [c for c in clients if c.code in code]
    # Client IDs is an integer prefixed with 'CLT', so let's sort list based
    # on the id integer value
    clients.sort(key=lambda c: int(c.id[3:]))
    if not json_output and verbose == 0:
        for c in clients:
            print(f'{c.id}: {c.name} [{c.code}]')
        return
    clients = [vars(c) for c in clients]
    if verbose == 0:
        fields = ('id', 'code', 'name')
        clients = [{k: v for k, v in c.items() if k in fields}
                   for c in clients]
    if json_output:
        print(json.dumps(clients))
        return
    # Verbose human readable output
    for c in clients:
        for k, v in c.items():
            if v is None:
                continue
            elif isinstance(v, list):
                print(f'{k}:\n    ' + '\n    '.join(v))
            else:
                print(f'{k}: {v}')
        print()


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover

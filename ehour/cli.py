# -*- coding: utf-8 -*-

"""Console script for ehour."""
import sys
import click
import datetime
from tabulate import tabulate

import ehour.api
from ehour.model import User, Client, Project


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
@click.option('--verbose', '-v', count=True,
              help='Verbose output.')
@click.option('--id', 'user_id', type=str, multiple=True,
              help='Filter on user ID.')
@click.pass_context
def users(ctx, verbose, user_id):
    ehour = connect(ctx.obj['api-key'], ctx.obj['config-file'])
    users = ehour.users()
    if user_id:
        users = [u for u in users if u.id in user_id]
    # User IDs is an integer prefixed with 'USR', so let's sort list based
    # on the id integer value
    users.sort(key=lambda c: int(c.id[3:]))
    print(tabulate([[u.id, u.name, u.email] for u in users],
                   headers=['Id', 'Name', 'Email']))


@cli.command()
@click.option('--verbose', '-v', count=True,
              help='Verbose output.')
@click.option('--id', 'client_id', type=str, multiple=True,
              help='Filter on client ID.')
@click.option('--code', type=str, multiple=True,
              help='Filter on client code field.')
@click.pass_context
def clients(ctx, verbose, client_id, code):
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
    if verbose:
        print_vertical(clients)
    else:
        print(tabulate([[c.id, c.code, c.name] for c in clients],
                       headers=['Id', 'Code', 'Name']))


@cli.command()
@click.option('--client', type=str,
              help='List only projects for client (id).')
@click.option('--inactive', is_flag=True,
              help='Include inactive projects.')
@click.option('--verbose', '-v', count=True,
              help='Verbose output.')
@click.pass_context
def projects(ctx, client, inactive, verbose):
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
    # Sort by client (id) first, and then project (id)
    projects.sort(key=lambda p: (int(p.client.id[3:]), int(p.id[3:])))
    if verbose:
        print_vertical(projects)
    else:
        print(tabulate([[p.id, p.code, p.name, p.client] for p in projects],
                       headers=['Id', 'Code', 'Name', 'Client']))


def print_vertical(elements):
    """Print list vertically.

    Print all fields, one per line, with blank line separating each
    list element.
    """
    elements = [vars(e) for e in elements]
    for element in elements:
        for key, value in element.items():
            if value is None:
                continue
            elif isinstance(value, list):
                print(f'{key}:\n    ' + '\n    '.join(value))
            elif type(value) in (str, int, bool):
                print(f'{key}: {value}')
            else:
                print(f'{key}: {value}')
        print()


def validate_date(ctx, param, value):
    """Callback for validation/conversion of date arguments."""
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise click.BadParameter('date must be in format YYYY-MM-DD')


@cli.command()
@click.argument('start', callback=validate_date)
@click.argument('end', callback=validate_date)
@click.option('--user', type=str,
              help='Only hours tracked for this user (id).')
@click.option('--client', type=str,
              help='Only hours tracked for this client (id).')
@click.option('--project', type=str,
              help='Only hours tracked on this project (id).')
@click.pass_context
def hours(ctx, start, end, user, client, project):
    ehour = connect(ctx.obj['api-key'], ctx.obj['config-file'])
    report = ehour.hours(start, end,
                         user=User.get(user) if user else None,
                         client=Client.get(client) if client else None,
                         project=Project.get(project) if project else None)
    rows = [[hours.date.isoformat(), hours.client.name, hours.project.name,
             hours.user.name, hours.hours.isoformat('minutes'),
             hours.rate, hours.turnover]
            for hours in report]
    headers = ['Date', 'Client', 'Project', 'User', 'Hours', 'Rate',
               'Turnover']
    colalign = ('left', 'left', 'left', 'left', 'center', 'right', 'right')
    print(tabulate(rows, headers=headers, floatfmt='.2f', colalign=colalign))


@cli.command()
@click.argument('start', callback=validate_date)
@click.argument('end', callback=validate_date)
@click.option('--user', type=str,
              help='Only expenses for this user (id).')
@click.option('--client', type=str,
              help='Only expenses for this client (id).')
@click.option('--project', type=str,
              help='Only expenses on this project (id).')
@click.pass_context
def expenses(ctx, start, end, user, client, project):
    ehour = connect(ctx.obj['api-key'], ctx.obj['config-file'])
    report = ehour.expenses(start, end,
                            user=User.get(user) if user else None,
                            client=Client.get(client) if client else None,
                            project=Project.get(project) if project else None)
    rows = [[exp.date.isoformat(), exp.client.name, exp.project.name,
             exp.user.name, exp.category.name, exp.name, exp.cost, exp.vat,
             exp.num_receipts if exp.num_receipts else '']
            for exp in report]
    headers = ['Date', 'Client', 'Project', 'User',
               'Category', 'Name', 'Cost', 'VAT', 'Receipts']
    colalign = ('left', 'left', 'left', 'left',
                'left', 'left', 'right', 'right', 'center')
    print(tabulate(rows, headers=headers, floatfmt='.2f', colalign=colalign))


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover

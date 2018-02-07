import click


CONTEXT_SETTINGS = dict(
    # Support -h as a shortcut for --help
    help_option_names=['-h', '--help'],
)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    pass

import click
from badges.generate import Generate

badge = Generate()


@click.group()
def cli():
    """CLI interface for Badge Creation"""


@cli.command(name="black")
def exe_black():
    badge.black()


@cli.command(name="lint")
def exe_lint():
    badge.pylint()


@cli.command(name="code_style")
def exe_code_style():
    badge.code_style()


@cli.command(name="safety")
def exe_safety():
    badge.safety()


if __name__ == "__main__":
    cli()

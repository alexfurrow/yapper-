import click
from flask.cli import with_appcontext
from backend.services.embedding import vectorize_all_entries

@click.command('vectorize-entries')
@with_appcontext
def vectorize_pages_command():  # Keep this name since app.py is importing it
    """Vectorize all entries."""
    click.echo('Vectorizing entries...')
    result = vectorize_all_entries()
    if result:
        click.echo('Vectorization complete!')
    else:
        click.echo('Vectorization failed.') 
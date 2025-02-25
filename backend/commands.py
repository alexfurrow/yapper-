import click
from flask.cli import with_appcontext
from backend.services.embedding import vectorize_all_pages

@click.command('vectorize-pages')
@with_appcontext
def vectorize_pages_command():
    """Vectorize all pages in the database."""
    click.echo('Vectorizing pages...')
    result = vectorize_all_pages()
    if result:
        click.echo('Vectorization complete!')
    else:
        click.echo('Vectorization failed.') 
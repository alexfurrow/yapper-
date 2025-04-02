import click
from flask.cli import with_appcontext
from backend.services.embedding import vectorize_all_entries

@click.command('vectorize-entries')
@with_appcontext
def vectorize_pages_command(): #for some reason when this is named "vectorize_entries_command()" I get a NameError, saying that "vectorize_pages_command" is not defined. so i'm trying to just rename it as the original name (I used to call 'entries' as 'pages') 
    """Vectorize all entries."""
    click.echo('Vectorizing entries...')
    result = vectorize_all_entries()
    if result:
        click.echo('Vectorization complete!')
    else:
        click.echo('Vectorization failed.') 
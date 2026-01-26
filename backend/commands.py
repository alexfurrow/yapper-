import click
from flask.cli import with_appcontext
from backend.services.embedding import vectorize_all_entries
from backend.routes.monthly_summaries import generate_summary_for_user, generate_summaries_for_previous_month
from supabase import create_client
import os

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

@click.command('generate-monthly-summary')
@click.option('--user-id', required=True, help='User ID (UUID)')
@click.option('--month', type=int, required=False, help='Month (1-12). Required if --year-only is not used.')
@click.option('--year', type=int, required=True, help='Year (e.g., 2025)')
@click.option('--year-only', is_flag=True, help='Generate summaries for all months in the year (skips existing summaries)')
@with_appcontext
def generate_monthly_summary_command(user_id, month, year, year_only):
    """Generate monthly summary for a specific user and month/year, or all months in a year."""
    import uuid
    
    # Validate inputs
    try:
        uuid.UUID(user_id)  # Validate UUID format
    except ValueError:
        click.echo(f'✗ Invalid user_id format. Must be a valid UUID.')
        raise click.Abort()
    
    if year < 2020 or year > 2100:
        click.echo(f'✗ Invalid year. Must be between 2020 and 2100.')
        raise click.Abort()
    
    # Create service Supabase client
    supabase = create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_SECRET_KEY")
    )
    
    # If --year-only flag is set, generate for all months
    if year_only:
        click.echo(f'Generating monthly summaries for user {user_id}, year {year}...')
        click.echo(f'This will check all 12 months and skip any that already have summaries.\n')
        
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        for m in range(1, 13):
            click.echo(f'Processing month {m}...', nl=False)
            
            success, message, data = generate_summary_for_user(user_id, m, year, supabase)
            
            if success:
                if 'already exists' in message.lower():
                    click.echo(f' ⏭  Skipped (already exists)')
                    skipped_count += 1
                else:
                    click.echo(f' ✓ {message}')
                    if data:
                        click.echo(f'   Entries: {len(data.get("list_of_entries", []))}')
                    success_count += 1
            else:
                if 'No entries found' in message:
                    click.echo(f' ⏭  Skipped (no entries)')
                    skipped_count += 1
                else:
                    click.echo(f' ✗ {message}')
                    failed_count += 1
        
        click.echo(f'\n--- Summary ---')
        click.echo(f'✓ Generated: {success_count}')
        click.echo(f'⏭  Skipped: {skipped_count}')
        if failed_count > 0:
            click.echo(f'✗ Failed: {failed_count}')
        
        if failed_count > 0:
            raise click.Abort()
    else:
        # Single month mode
        if month is None:
            click.echo(f'✗ --month is required when --year-only is not used.')
            raise click.Abort()
        
        if month < 1 or month > 12:
            click.echo(f'✗ Invalid month. Must be between 1 and 12.')
            raise click.Abort()
        
        click.echo(f'Generating monthly summary for user {user_id}, month {month}, year {year}...')
        
        success, message, data = generate_summary_for_user(user_id, month, year, supabase)
        
        if success:
            click.echo(f'✓ {message}')
            if data:
                click.echo(f'Summary ID: {data.get("id")}')
                click.echo(f'Month/Year: {data.get("month_year")}')
                click.echo(f'Entries: {len(data.get("list_of_entries", []))}')
        else:
            click.echo(f'✗ {message}')
            raise click.Abort()

@click.command('generate-all-monthly-summaries')
@with_appcontext
def generate_all_monthly_summaries_command():
    """Generate monthly summaries for all users for the previous month."""
    click.echo('Generating monthly summaries for previous month...')
    try:
        generate_summaries_for_previous_month()
        click.echo('✓ Monthly summary generation complete!')
    except Exception as e:
        click.echo(f'✗ Error: {str(e)}')
        raise click.Abort() 
"""CLI tool for testing Bot X functionality."""

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from sqlalchemy import text

from app.core.database import SessionLocal, init_db, Question
from app.services.embedding import get_embedding
from app.services.responder import clean_tweet_text, find_best_match, process_mention
from app.bot.factory import get_worker_by_platform
from app.bot.base import Mention
from app.core.config import settings
from datetime import datetime, timezone

console = Console()


@click.group()
def cli():
    """Bot X - CLI tool for testing bot functionality."""
    pass


@cli.command()
def test_db():
    """Test database connection and pgvector extension."""
    console.print("[bold blue]Testing database connection...[/bold blue]")

    try:
        db = SessionLocal()

        # Test basic connection
        result = db.execute(text("SELECT 1")).fetchone()
        console.print("✓ Database connection: [green]OK[/green]")

        # Test pgvector extension
        result = db.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'")).fetchone()
        if result:
            console.print("✓ pgvector extension: [green]Installed[/green]")
        else:
            console.print("✗ pgvector extension: [red]Not installed[/red]")
            console.print("  Run: CREATE EXTENSION IF NOT EXISTS vector;")

        # Check tables
        result = db.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )).fetchall()

        if result:
            console.print(f"✓ Tables found: [green]{len(result)}[/green]")
            for table in result:
                console.print(f"  - {table[0]}")
        else:
            console.print("✗ No tables found. Run: [yellow]botx init-db[/yellow]")

        db.close()

    except Exception as e:
        console.print(f"✗ Database error: [red]{str(e)}[/red]")


@cli.command()
def init_db_cmd():
    """Initialize database tables."""
    console.print("[bold blue]Initializing database...[/bold blue]")

    try:
        init_db()
        console.print("✓ Database initialized: [green]OK[/green]")
    except Exception as e:
        console.print(f"✗ Initialization error: [red]{str(e)}[/red]")


@cli.command()
def test_openai():
    """Test OpenAI API connection and embedding generation."""
    console.print("[bold blue]Testing OpenAI API...[/bold blue]")

    try:
        test_text = "Hello, this is a test message"
        console.print(f"Generating embedding for: '{test_text}'")

        embedding = get_embedding(test_text)

        console.print(f"✓ OpenAI API: [green]OK[/green]")
        console.print(f"  Model: {settings.embedding_model}")
        console.print(f"  Embedding dimensions: {len(embedding)}")
        console.print(f"  First 5 values: {embedding[:5]}")

    except Exception as e:
        console.print(f"✗ OpenAI API error: [red]{str(e)}[/red]")


@cli.command()
def test_twitter():
    """Test Twitter API connection."""
    console.print("[bold blue]Testing Twitter API...[/bold blue]")

    try:
        worker = get_worker_by_platform("twitter")
        if not worker:
            console.print("✗ Twitter worker: [red]Failed to initialize[/red]")
            return

        # Try to fetch mentions (will return empty if none, but tests connection)
        mentions = worker.check_mentions()

        console.print("✓ Twitter API: [green]OK[/green]")
        console.print(f"  Bot ID: {settings.twitter_bot_id}")
        console.print(f"  Bot username: {worker.get_bot_username()}")
        console.print(f"  Recent mentions: {len(mentions)}")

    except Exception as e:
        console.print(f"✗ Twitter API error: [red]{str(e)}[/red]")


@cli.command()
def test_bluesky():
    """Test Bluesky API connection."""
    console.print("[bold blue]Testing Bluesky API...[/bold blue]")

    try:
        worker = get_worker_by_platform("bluesky")
        if not worker:
            console.print("✗ Bluesky worker: [red]Failed to initialize[/red]")
            console.print("  Make sure atproto package is installed and credentials are configured")
            return

        # Try to fetch mentions (will return empty if none, but tests connection)
        mentions = worker.check_mentions()

        console.print("✓ Bluesky API: [green]OK[/green]")
        console.print(f"  Bot handle: {settings.bluesky_handle}")
        console.print(f"  Service URL: {settings.bluesky_service_url}")
        console.print(f"  Recent mentions: {len(mentions)}")

    except Exception as e:
        console.print(f"✗ Bluesky API error: [red]{str(e)}[/red]")


@cli.command()
@click.argument('platform')
def test_platform(platform):
    """Test a specific platform API connection."""
    console.print(f"[bold blue]Testing {platform.capitalize()} API...[/bold blue]")

    try:
        worker = get_worker_by_platform(platform)
        if not worker:
            console.print(f"✗ {platform} worker: [red]Failed to initialize[/red]")
            return

        # Try to fetch mentions
        mentions = worker.check_mentions()

        console.print(f"✓ {platform.capitalize()} API: [green]OK[/green]")
        console.print(f"  Bot username: {worker.get_bot_username()}")
        console.print(f"  Recent mentions: {len(mentions)}")

    except Exception as e:
        console.print(f"✗ {platform.capitalize()} API error: [red]{str(e)}[/red]")


@cli.command()
@click.option('--question', '-q', required=True, help='Question text')
@click.option('--answer', '-a', required=True, help='Answer text')
def add_qa(question, answer):
    """Add a question-answer pair to the database."""
    console.print(f"[bold blue]Adding Q&A pair...[/bold blue]")

    try:
        db = SessionLocal()

        # Generate embedding
        embedding = get_embedding(question)

        # Create question record
        qa = Question(
            question=question,
            answer=answer,
            embedding=embedding
        )

        db.add(qa)
        db.commit()
        db.refresh(qa)

        console.print(f"✓ Added Q&A pair: [green]ID {qa.id}[/green]")
        console.print(f"  Q: {question}")
        console.print(f"  A: {answer}")

        db.close()

    except Exception as e:
        console.print(f"✗ Error adding Q&A: [red]{str(e)}[/red]")


@cli.command()
def list_qa():
    """List all question-answer pairs in the database."""
    console.print("[bold blue]Question-Answer Pairs[/bold blue]\n")

    try:
        db = SessionLocal()
        questions = db.query(Question).all()

        if not questions:
            console.print("[yellow]No Q&A pairs found. Add some with: botx add-qa[/yellow]")
            db.close()
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Question", width=40)
        table.add_column("Answer", width=40)
        table.add_column("Created", width=20)

        for q in questions:
            table.add_row(
                str(q.id),
                q.question[:37] + "..." if len(q.question) > 40 else q.question,
                q.answer[:37] + "..." if len(q.answer) > 40 else q.answer,
                q.created_at.strftime("%Y-%m-%d %H:%M:%S")
            )

        console.print(table)
        console.print(f"\n[green]Total: {len(questions)} pairs[/green]")

        db.close()

    except Exception as e:
        console.print(f"✗ Error listing Q&A: [red]{str(e)}[/red]")


@cli.command()
@click.argument('text')
def test_match(text):
    """Test similarity matching for a given text."""
    console.print(f"[bold blue]Testing similarity match...[/bold blue]")
    console.print(f"Input: '{text}'\n")

    try:
        db = SessionLocal()

        # Generate embedding
        embedding = get_embedding(text)
        console.print("✓ Generated embedding")

        # Find match
        match = find_best_match(db, embedding)

        if match:
            answer, similarity = match
            console.print(f"\n✓ Match found! [green]Similarity: {similarity:.4f}[/green]")
            console.print(f"  Answer: {answer}")

            if similarity < settings.similarity_threshold:
                console.print(f"\n[yellow]Note: Similarity below threshold ({settings.similarity_threshold})[/yellow]")
        else:
            console.print(f"\n✗ No match found above threshold ([yellow]{settings.similarity_threshold}[/yellow])")

        db.close()

    except Exception as e:
        console.print(f"✗ Error testing match: [red]{str(e)}[/red]")


@cli.command()
@click.argument('tweet_text')
@click.option('--platform', '-p', default='twitter', help='Platform (twitter, bluesky)')
@click.option('--mention-id', default='test_123', help='Mention ID for testing')
def simulate_mention(tweet_text, platform, mention_id):
    """Simulate processing a mention from any platform."""
    console.print(f"[bold blue]Simulating {platform} mention processing...[/bold blue]")
    console.print(f"Mention ID: {mention_id}")
    console.print(f"Text: '{tweet_text}'\n")

    try:
        db = SessionLocal()

        # Get the platform worker
        worker = get_worker_by_platform(platform)
        if not worker:
            console.print(f"✗ {platform} worker: [red]Failed to initialize[/red]")
            return

        bot_username = worker.get_bot_username()

        # Create a mock Mention object
        mention = Mention(
            id=mention_id,
            text=tweet_text,
            author_id="test_author",
            created_at=datetime.now(timezone.utc),
            platform=platform
        )

        # Clean text
        cleaned = clean_tweet_text(mention.text, bot_username)
        console.print(f"✓ Cleaned text: '{cleaned}'")

        # Generate embedding
        embedding = get_embedding(cleaned)
        console.print("✓ Generated embedding")

        # Find match
        match = find_best_match(db, embedding)

        if match:
            answer, similarity = match
            console.print(f"\n✓ Match found! [green]Similarity: {similarity:.4f}[/green]")
            console.print(f"  Would reply with: '{answer}'")

            if similarity >= settings.similarity_threshold:
                console.print(f"\n[green]✓ Would post reply (above threshold)[/green]")
            else:
                console.print(f"\n[yellow]✗ Would NOT reply (below threshold {settings.similarity_threshold})[/yellow]")
        else:
            console.print(f"\n✗ No match found")

        db.close()

    except Exception as e:
        console.print(f"✗ Error simulating mention: [red]{str(e)}[/red]")


@cli.command()
def test_all():
    """Run all tests to verify bot is working correctly."""
    console.print("[bold cyan]Running all Bot X tests...[/bold cyan]\n")

    # Base tests
    tests = [
        ("Database Connection", test_db),
        ("OpenAI API", test_openai),
    ]

    # Add platform tests based on enabled platforms
    enabled_platforms = settings.get_enabled_platforms
    if "twitter" in enabled_platforms:
        tests.append(("Twitter API", test_twitter))
    if "bluesky" in enabled_platforms:
        tests.append(("Bluesky API", test_bluesky))

    for test_name, test_func in tests:
        console.print(f"\n{'='*60}")
        console.print(f"[bold]{test_name}[/bold]")
        console.print('='*60)

        try:
            ctx = click.Context(test_func)
            ctx.invoke(test_func)
        except Exception as e:
            console.print(f"✗ Test failed: [red]{str(e)}[/red]")

        console.print()

    console.print("\n[bold green]All tests completed![/bold green]")


@cli.command()
def config():
    """Show current configuration."""
    console.print("[bold blue]Bot X Configuration[/bold blue]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan", width=30)
    table.add_column("Value", width=50)

    # Safe settings to display
    safe_settings = [
        ("Database URL", settings.database_url.replace(settings.database_url.split('@')[0].split('://')[1], '***') if '@' in settings.database_url else settings.database_url),
        ("OpenAI API Key", settings.openai_api_key[:10] + "..." if settings.openai_api_key else "[red]Not set[/red]"),
        ("Embedding Model", settings.embedding_model),
        ("Similarity Threshold", str(settings.similarity_threshold)),
        ("Enabled Platforms", ", ".join(settings.get_enabled_platforms)),
        ("", ""),  # Separator
        ("Twitter Bot ID", settings.twitter_bot_id if settings.twitter_bot_id else "[yellow]Not set[/yellow]"),
        ("Bluesky Handle", settings.bluesky_handle if settings.bluesky_handle else "[yellow]Not set[/yellow]"),
        ("Bluesky Service URL", settings.bluesky_service_url),
    ]

    for setting, value in safe_settings:
        table.add_row(setting, value)

    console.print(table)


if __name__ == "__main__":
    cli()

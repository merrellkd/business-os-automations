# Create interfaces/cli.py

import click
import yaml
from pathlib import Path
from typing import Dict, Any

from ..flow import run_full_index, run_query, run_test_query


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "default_config.yaml"
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


@click.group()
def cli():
    """Semantic Search CLI for business-os documents."""
    pass


@cli.command()
@click.option('--config', '-c', help='Config file path')
@click.option('--root-path', '-r', help='Root directory to index')
@click.option('--incremental', '-i', is_flag=True, help='Run incremental indexing')
def index(config, root_path, incremental):
    """Run the indexing flow to process documents."""
    
    config_data = load_config(config)
    
    if root_path:
        config_data['root_path'] = root_path
    
    shared = {"config": config_data}
    
    click.echo("Starting indexing process...")
    
    if incremental:
        # For now, incremental just runs full index
        click.echo("Running incremental indexing...")
    else:
        click.echo("Running full indexing...")
    
    try:
        run_full_index(shared)
        click.echo("✅ Indexing completed successfully!")
        
        # Show stats
        files_indexed = len(shared.get("indexing", {}).get("filtered_files", []))
        chunks_created = len(shared.get("indexing", {}).get("chunks", []))
        click.echo(f"📊 Processed {files_indexed} files, created {chunks_created} chunks")
        
    except Exception as e:
        click.echo(f"❌ Indexing failed: {e}")
        raise click.Abort()


@cli.command()
@click.option('--config', '-c', help='Config file path')
@click.option('--output', '-o', help='Output file path (default: console)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive search mode')
def search(config, output, interactive):
    """Search indexed documents."""
    
    config_data = load_config(config)
    
    if output:
        config_data['output_format'] = 'file'
    
    if interactive:
        click.echo("🔍 Interactive Search Mode (type 'quit' to exit)")
        while True:
            query = click.prompt("\nEnter your question", type=str)
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            try:
                result = run_test_query(query, config_data)
                click.echo(f"\n💬 Answer: {result}")
            except Exception as e:
                click.echo(f"❌ Search failed: {e}")
    else:
        query = click.prompt("Enter your question", type=str)
        try:
            result = run_test_query(query, config_data)
            
            if output:
                Path(output).write_text(result)
                click.echo(f"📝 Response written to: {output}")
            else:
                click.echo(f"\n💬 Answer: {result}")
        except Exception as e:
            click.echo(f"❌ Search failed: {e}")
            raise click.Abort()


@cli.command()
@click.argument('query')
@click.option('--config', '-c', help='Config file path')
@click.option('--output', '-o', help='Output file path')
def ask(query, config, output):
    """Ask a single question."""
    
    config_data = load_config(config)
    
    if output:
        config_data['output_format'] = 'file'
    
    try:
        result = run_test_query(query, config_data)
        
        if output:
            Path(output).write_text(result)
            click.echo(f"📝 Response written to: {output}")
        else:
            click.echo(result)
    except Exception as e:
        click.echo(f"❌ Query failed: {e}")
        raise click.Abort()


@cli.command()
@click.option('--config', '-c', help='Config file to edit')
def config_cmd(config):
    """Manage configuration settings."""
    
    config_path = config or (Path(__file__).parent.parent / "config" / "default_config.yaml")
    
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            current_config = yaml.safe_load(f)
        
        click.echo("Current configuration:")
        click.echo(yaml.dump(current_config, default_flow_style=False))
    else:
        click.echo(f"Config file not found: {config_path}")


if __name__ == '__main__':
    cli()
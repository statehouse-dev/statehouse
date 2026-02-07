"""
Statehouse CLI (statehousectl)

Command-line interface for interacting with Statehouse daemon.
"""

import json
import sys
from datetime import datetime

import click

from statehouse import Statehouse
from statehouse.exceptions import StatehouseError


@click.group()
@click.option('--address', default='localhost:50051', help='Statehouse daemon address')
@click.pass_context
def cli(ctx, address):
    """Statehouse CLI - interact with the Statehouse daemon"""
    ctx.ensure_object(dict)
    ctx.obj['address'] = address


@cli.command()
@click.pass_context
def health(ctx):
    """Check daemon health status"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        status = client.health()
        if status == "ok":
            click.echo(click.style('✓ Daemon is healthy', fg='green'))
            sys.exit(0)
        else:
            click.echo(click.style(f'✗ Daemon returned: {status}', fg='yellow'))
            sys.exit(1)
    except Exception as e:
        click.echo(click.style(f'✗ Connection failed: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx):
    """Get daemon version"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        version, git_sha = client.version()
        click.echo(f"Version: {version}")
        click.echo(f"Git SHA: {git_sha}")
    except Exception as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.argument('key')
@click.option('--namespace', default='default', help='Namespace')
@click.option('--json-output', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def get(ctx, agent_id, key, namespace, output_json):
    """Get state value for agent_id and key"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        result = client.get_state(
            agent_id=agent_id,
            key=key,
            namespace=namespace
        )
        
        if not result.exists or result.value is None:
            click.echo(click.style('✗ Key not found', fg='yellow'))
            sys.exit(1)
        
        if output_json:
            output = {
                'key': key,
                'version': result.version,
                'commit_ts': result.commit_ts,
                'value': result.value
            }
            click.echo(json.dumps(output, indent=2))
        else:
            click.echo(f"Key:       {key}")
            click.echo(f"Version:   {result.version}")
            click.echo(f"Commit TS: {result.commit_ts}")
            click.echo(f"\nValue:")
            click.echo(json.dumps(result.value, indent=2))
    
    except StatehouseError as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.option('--namespace', default='default', help='Namespace')
@click.option('--prefix', help='Filter keys by prefix')
@click.pass_context
def keys(ctx, agent_id, namespace, prefix):
    """List keys for an agent"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        
        if prefix:
            results = client.scan_prefix(
                agent_id=agent_id,
                prefix=prefix,
                namespace=namespace
            )
            keys_list = [f"{prefix}{i}" for i in range(len(results))]
        else:
            keys_list = client.list_keys(
                agent_id=agent_id,
                namespace=namespace
            )
        
        if keys_list:
            click.echo(f"Keys for agent '{agent_id}' (namespace: {namespace}):")
            for key in keys_list:
                click.echo(f"  - {key}")
            click.echo(f"\nTotal: {len(keys_list)}")
        else:
            click.echo(f"No keys found for agent '{agent_id}'")
    
    except StatehouseError as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.option('--namespace', default='default', help='Namespace')
@click.option('--start-ts', type=int, help='Start timestamp')
@click.option('--end-ts', type=int, help='End timestamp')
@click.option('--limit', type=int, help='Limit number of events')
@click.pass_context
def replay(ctx, agent_id, namespace, start_ts, end_ts, limit):
    """Replay events for an agent"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        
        events = client.replay(
            agent_id=agent_id,
            namespace=namespace,
            start_ts=start_ts,
            end_ts=end_ts
        )
        
        count = 0
        for event in events:
            if limit and count >= limit:
                break
            
            click.echo(f"\n--- Event (commit_ts={event.commit_ts}, txn_id={event.txn_id}) ---")
            for op in event.operations:
                if op.value is not None:
                    click.echo(f"  Write: {op.key} (version {op.version})")
                    click.echo(f"    Value: {json.dumps(op.value)}")
                else:
                    click.echo(f"  Delete: {op.key} (version {op.version})")
            count += 1
        
        if count == 0:
            click.echo(f"No events found for agent '{agent_id}'")
        else:
            click.echo(f"\nTotal events: {count}")
    
    except StatehouseError as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.option('--namespace', default='default', help='Namespace')
@click.option('--follow', '-f', is_flag=True, help='Follow mode (not yet implemented)')
@click.pass_context
def tail(ctx, agent_id, namespace, follow):
    """Tail recent events (like replay but focused on recent)"""
    address = ctx.obj['address']
    
    if follow:
        click.echo(click.style('Follow mode not yet implemented', fg='yellow'))
        sys.exit(1)
    
    try:
        client = Statehouse(url=address)
        
        # Get last 10 events
        events = list(client.replay(
            agent_id=agent_id,
            namespace=namespace
        ))
        
        # Take last 10
        recent = events[-10:] if len(events) > 10 else events
        
        if recent:
            click.echo(f"Last {len(recent)} events for agent '{agent_id}':")
            for event in recent:
                timestamp = datetime.fromtimestamp(event.commit_ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
                click.echo(f"\n[{timestamp}] txn_id={event.txn_id}")
                for op in event.operations:
                    if op.value is not None:
                        click.echo(f"  ✏️  Write: {op.key}")
                    else:
                        click.echo(f"  ❌ Delete: {op.key}")
        else:
            click.echo(f"No events found for agent '{agent_id}'")
    
    except StatehouseError as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('agent_id')
@click.option('--namespace', default='default', help='Namespace')
@click.option('--output', '-o', help='Output file (default: stdout)')
@click.option('--format', 'output_format', type=click.Choice(['json', 'text']), default='json', help='Output format')
@click.pass_context
def dump(ctx, agent_id, namespace, output, output_format):
    """Dump all state for an agent"""
    address = ctx.obj['address']
    
    try:
        client = Statehouse(url=address)
        
        # Get all keys
        keys_list = client.list_keys(agent_id=agent_id, namespace=namespace)
        
        # Fetch all values
        state_dump = {}
        for key in keys_list:
            result = client.get_state(agent_id=agent_id, key=key, namespace=namespace)
            if result.exists and result.value is not None:
                state_dump[key] = {
                    'value': result.value,
                    'version': result.version,
                    'commit_ts': result.commit_ts
                }
        
        # Format output
        if output_format == 'json':
            output_str = json.dumps(state_dump, indent=2)
        else:
            lines = [f"State dump for agent '{agent_id}' (namespace: {namespace})\n"]
            for key, data in state_dump.items():
                lines.append(f"\n{key}:")
                lines.append(f"  Version: {data['version']}")
                lines.append(f"  Commit TS: {data['commit_ts']}")
                lines.append(f"  Value: {json.dumps(data['value'])}")
            output_str = '\n'.join(lines)
        
        # Write to file or stdout
        if output:
            with open(output, 'w') as f:
                f.write(output_str)
            click.echo(f"✓ State dumped to {output}")
        else:
            click.echo(output_str)
    
    except StatehouseError as e:
        click.echo(click.style(f'✗ Error: {e}', fg='red'))
        sys.exit(1)


def main():
    """Entry point for CLI"""
    cli(obj={})


if __name__ == '__main__':
    main()

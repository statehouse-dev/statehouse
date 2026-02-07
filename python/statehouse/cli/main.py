"""
Statehouse CLI (statehousectl)

Command-line interface for interacting with Statehouse daemon.
"""

import json
import sys

import click

from statehouse import Statehouse
from statehouse.exceptions import StatehouseError


@click.group()
@click.option("--address", default="localhost:50051", help="Statehouse daemon address")
@click.pass_context
def cli(ctx, address):
    """Statehouse CLI - interact with the Statehouse daemon"""
    ctx.ensure_object(dict)
    ctx.obj["address"] = address


@cli.command()
@click.pass_context
def health(ctx):
    """Check daemon health status"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)
        status = client.health()
        if status == "ok":
            click.echo(click.style("✓ Daemon is healthy", fg="green"))
            sys.exit(0)
        else:
            click.echo(click.style(f"✗ Daemon returned: {status}", fg="yellow"))
            sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"✗ Connection failed: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.pass_context
def version(ctx):
    """Get daemon version"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)
        version, git_sha = client.version()
        click.echo(f"Version: {version}")
        click.echo(f"Git SHA: {git_sha}")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.argument("key")
@click.option("--namespace", default="default", help="Namespace")
@click.option("--json-output", "output_json", is_flag=True, help="Output as JSON")
@click.option("--pretty", is_flag=True, help="Pretty-print the value")
@click.pass_context
def get(ctx, agent_id, key, namespace, output_json, pretty):
    """Get state value for agent_id and key"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)
        result = client.get_state(agent_id=agent_id, key=key, namespace=namespace)

        if not result.exists or result.value is None:
            click.echo(click.style("✗ Key not found", fg="yellow"))
            sys.exit(1)

        if output_json:
            output = {"key": key, "version": result.version, "commit_ts": result.commit_ts, "value": result.value}
            click.echo(json.dumps(output, indent=2))
        elif pretty:
            # Pretty format using value summary
            from statehouse.formatting import format_ts, format_value_summary

            click.echo(f"Key:       {key}")
            click.echo(f"Version:   {result.version}")
            click.echo(f"Timestamp: {format_ts(result.commit_ts)}")
            click.echo(f"\nValue: {format_value_summary(result.value, max_len=200)}")
        else:
            click.echo(f"Key:       {key}")
            click.echo(f"Version:   {result.version}")
            click.echo(f"Commit TS: {result.commit_ts}")
            click.echo("\nValue:")
            click.echo(json.dumps(result.value, indent=2))

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--namespace", default="default", help="Namespace")
@click.option("--prefix", help="Filter keys by prefix")
@click.pass_context
def keys(ctx, agent_id, namespace, prefix):
    """List keys for an agent"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)

        if prefix:
            results = client.scan_prefix(agent_id=agent_id, prefix=prefix, namespace=namespace)
            keys_list = [f"{prefix}{i}" for i in range(len(results))]
        else:
            keys_list = client.list_keys(agent_id=agent_id, namespace=namespace)

        if keys_list:
            click.echo(f"Keys for agent '{agent_id}' (namespace: {namespace}):")
            for key in keys_list:
                click.echo(f"  - {key}")
            click.echo(f"\nTotal: {len(keys_list)}")
        else:
            click.echo(f"No keys found for agent '{agent_id}'")

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--namespace", default="default", help="Namespace")
@click.option("--start-ts", type=int, help="Start timestamp")
@click.option("--end-ts", type=int, help="End timestamp")
@click.option("--limit", type=int, help="Limit number of events")
@click.option("--verbose", is_flag=True, help="Show full details (txn_id, event_id, payload)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON lines")
@click.pass_context
def replay(ctx, agent_id, namespace, start_ts, end_ts, limit, verbose, output_json):
    """Replay events for an agent (pretty format by default)"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)

        if output_json:
            # JSON output mode
            events = client.replay(agent_id=agent_id, namespace=namespace, start_ts=start_ts, end_ts=end_ts)

            count = 0
            for event in events:
                if limit and count >= limit:
                    break

                # Output event as JSON line
                event_dict = event.to_dict()
                click.echo(json.dumps(event_dict))
                count += 1
        else:
            # Pretty output mode (default)
            lines = client.replay_pretty(
                agent_id=agent_id,
                namespace=namespace,
                start_ts=start_ts,
                end_ts=end_ts,
                verbose=verbose,
            )

            count = 0
            for line in lines:
                if limit and count >= limit:
                    break
                click.echo(line)
                count += 1

        if count == 0:
            click.echo(f"No events found for agent '{agent_id}'")

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--namespace", default="default", help="Namespace")
@click.option("--lines", "-n", type=int, default=10, help="Number of recent events to show")
@click.option("--follow", "-f", is_flag=True, help="Follow mode (not yet implemented)")
@click.pass_context
def tail(ctx, agent_id, namespace, lines, follow):
    """Show recent events using pretty replay format"""
    address = ctx.obj["address"]

    if follow:
        click.echo(click.style("Follow mode not yet implemented", fg="yellow"))
        sys.exit(1)

    try:
        client = Statehouse(url=address)

        # Get all events
        all_lines = list(client.replay_pretty(agent_id=agent_id, namespace=namespace))

        # Take last N lines
        recent = all_lines[-lines:] if len(all_lines) > lines else all_lines

        if recent:
            for line in recent:
                click.echo(line)
        else:
            click.echo(f"No events found for agent '{agent_id}'")

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--namespace", default="default", help="Namespace")
@click.option("--output", "-o", help="Output file (default: stdout)")
@click.option("--format", "output_format", type=click.Choice(["json", "text"]), default="json", help="Output format")
@click.pass_context
def dump(ctx, agent_id, namespace, output, output_format):
    """Dump all state for an agent"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)

        # Get all keys
        keys_list = client.list_keys(agent_id=agent_id, namespace=namespace)

        # Fetch all values
        state_dump = {}
        for key in keys_list:
            result = client.get_state(agent_id=agent_id, key=key, namespace=namespace)
            if result.exists and result.value is not None:
                state_dump[key] = {"value": result.value, "version": result.version, "commit_ts": result.commit_ts}

        # Format output
        if output_format == "json":
            output_str = json.dumps(state_dump, indent=2)
        else:
            lines = [f"State dump for agent '{agent_id}' (namespace: {namespace})\n"]
            for key, data in state_dump.items():
                lines.append(f"\n{key}:")
                lines.append(f"  Version: {data['version']}")
                lines.append(f"  Commit TS: {data['commit_ts']}")
                lines.append(f"  Value: {json.dumps(data['value'])}")
            output_str = "\n".join(lines)

        # Write to file or stdout
        if output:
            with open(output, "w") as f:
                f.write(output_str)
            click.echo(f"✓ State dumped to {output}")
        else:
            click.echo(output_str)

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("agent_id")
@click.option("--namespace", default="default", help="Namespace")
@click.pass_context
def inspect(ctx, agent_id, namespace):
    """Show agent summary (keys, recent activity, stats)"""
    address = ctx.obj["address"]

    try:
        client = Statehouse(url=address)

        # Get all keys
        keys_list = client.list_keys(agent_id=agent_id, namespace=namespace)

        # Get recent events
        all_events = list(client.replay_events(agent_id=agent_id, namespace=namespace))
        recent_events = all_events[-5:] if len(all_events) > 5 else all_events

        # Display summary
        click.echo(click.style(f"\n=== Agent Inspect: {agent_id} ===", fg="cyan", bold=True))
        click.echo(f"Namespace: {namespace}")
        click.echo(f"\nTotal Keys: {len(keys_list)}")

        if keys_list:
            click.echo("\nKeys (showing first 10):")
            for key in keys_list[:10]:
                click.echo(f"  • {key}")
            if len(keys_list) > 10:
                click.echo(f"  ... and {len(keys_list) - 10} more")

        click.echo(f"\nTotal Events: {len(all_events)}")

        if recent_events:
            click.echo(f"\nRecent Activity (last {len(recent_events)} events):")
            for line in client.replay_pretty(agent_id=agent_id, namespace=namespace):
                # Only show recent
                if recent_events:
                    click.echo(f"  {line}")
                    recent_events = recent_events[1:]
                else:
                    break

        click.echo()

    except StatehouseError as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


def main():
    """Entry point for CLI"""
    cli(obj={})


if __name__ == "__main__":
    main()

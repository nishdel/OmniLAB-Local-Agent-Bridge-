import argparse
import json
import time
from .config import load_config
from .telemetry import Store, configure_logging


def main():
    parser = argparse.ArgumentParser(description="Local coding companion, Ollama MCP bridge and usage monitor")
    parser.add_argument("--config", help="TOML config path (or LAB_CONFIG)")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("server", help="Run the MCP server over stdio")
    collector = commands.add_parser("collector", help="Run metadata collection without the widget")
    collector.add_argument("--backfill", action="store_true", help="Import retained historical rollouts")
    collector.add_argument("--once", action="store_true", help="One bounded rollout scan, then exit")
    commands.add_parser("widget", help="Run the Windows tray widget with its collector")
    commands.add_parser("dashboard", help="Alias for the Windows tray widget")
    commands.add_parser("doctor", help="Check runtime, local models, storage and registration")
    commands.add_parser("codex-config", help="Print this installation's MCP TOML; does not edit Codex")
    commands.add_parser("stats", help="Print aggregate usage JSON")
    smoke_parser = commands.add_parser("smoke", help="Call legacy tools over MCP, or all v0.2 capabilities")
    smoke_parser.add_argument("--all", action="store_true", help="Exercise all seven capabilities")
    smoke_parser.add_argument("--consensus", action="store_true", help="Also exercise the configured consensus roles")
    commands.add_parser("models", help="Check configured role models; print exact install commands for missing models")
    commands.add_parser("verify-models", help="Verify every configured role/model with real local inference")
    workflow_parser = commands.add_parser('workflow', help='Opt-in bounded role/workflow operations')
    workflow_parser.add_argument('action', choices=['catalog','plan','start','step','checkpoint','status'])
    workflow_parser.add_argument('--request', help='JSON object with the operation arguments; no commands are executed')
    from .companion_cli import add_parser
    add_parser(commands)
    args = parser.parse_args()
    config = load_config(args.config)
    configure_logging(config)
    if args.command == 'companion':
        from .companion_cli import run
        run(args, config)
    elif args.command == 'workflow':
        import asyncio
        from pathlib import Path
        from .service import Service
        engine = Service(config).workflows
        if engine is None:
            parser.exit(1, 'Workflow support is disabled; configure [agentic].\n')
        payload = {}
        if args.request:
            with Path(args.request).open('rb') as stream:
                raw = stream.read(200001)
            if len(raw)>200000:
                parser.exit(1, 'Workflow request exceeds 200,000 bytes.\n')
            payload = json.loads(raw)
        function = engine.catalog.inspect if args.action=='catalog' else getattr(engine,args.action)
        result = function(**payload)
        if args.action=='step':
            result = asyncio.run(result)
        print(json.dumps(result,indent=2))
    elif args.command == "server":
        from .server import create_server
        create_server(config).run(transport="stdio")
    elif args.command in ("widget", "dashboard"):
        from .widget import run_widget
        run_widget(config)
    elif args.command in ('doctor', 'codex-config'):
        import asyncio
        from .setup import doctor, codex_config, config_path
        path = config_path(args.config)
        if args.command == 'codex-config':
            print(codex_config(config, path))
        else:
            checks = asyncio.run(doctor(config, path))
            print(json.dumps(checks, indent=2))
            if any(row['status']=='error' for row in checks):
                raise SystemExit(1)
    elif args.command == "stats":
        print(json.dumps(Store(config.data_dir).totals(), indent=2))
    elif args.command == "smoke":
        import asyncio
        from .smoke import smoke
        asyncio.run(smoke(args.config, args.all, args.consensus))
    elif args.command in ("models", "verify-models"):
        import asyncio
        import httpx
        try:
            if args.command == "models":
                from .routing import model_status
                from .models import registry_status
                rows = asyncio.run(registry_status(config) if config.model_registry else model_status(config))
                print(json.dumps(rows, indent=2))
                if not all(row["installed"] for row in rows):
                    raise SystemExit(1)
            else:
                from .verify import verify_models
                if not asyncio.run(verify_models(config)):
                    raise SystemExit(1)
        except (httpx.HTTPError, ValueError):
            parser.exit(1, "Ollama model inventory is unavailable or invalid. Start Ollama and check /api/tags.\n")
    else:
        from .collector import Collector
        instance = Collector(config, args.backfill)
        if args.once:
            instance.reader.poll()
        else:
            instance.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                instance.close()


if __name__ == "__main__":
    main()

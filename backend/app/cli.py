"""Command-line access to the same seeding the workshop UI runs.

python -m app.cli seed all            # pinecone, langfuse, datahub
python -m app.cli seed langfuse       # one step
python -m app.cli datahub-token       # create a DataHub token with datahub/datahub
python -m app.cli status
"""

import argparse
import asyncio
import json
import sys

from app.connectors.registry import CONNECTORS
from app.deps import get_store
from app.seed.steps import STEPS, run_step
from app.services.datahub_api import DataHubError, create_access_token

_COLORS = {"success": "\033[32m", "error": "\033[31m", "detail": "\033[90m"}


async def seed(steps: list[str]) -> int:
    for step_id in steps:
        print(f"\n▶ {STEPS[step_id].title}")
        ok = False
        async for e in run_step(step_id):
            if e["type"] == "log":
                color = _COLORS.get(e["level"], "")
                print(f"  {color}{e['message']}\033[0m" if color else f"  {e['message']}")
            elif e["type"] == "end":
                ok = e["ok"]
        if not ok:
            return 1
    return 0


async def datahub_token(username: str, password: str) -> int:
    store = get_store()
    connector = CONNECTORS["datahub"]
    try:
        token = await create_access_token(store.resolve(connector, {})["ui_url"], username, password)
    except DataHubError as e:
        print(e, file=sys.stderr)
        return 1
    store.save(connector, {"token": token})
    result = await connector.test(store.resolve(connector, {}))
    store.record_check(connector.id, result)
    print(result.message)
    return 0 if result.ok else 1


async def status() -> int:
    from app.routers.system import status as status_route

    print(json.dumps(await status_route(), indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    p_seed = sub.add_parser("seed", help="Run seed steps")
    p_seed.add_argument("step", choices=["all", *STEPS])
    p_token = sub.add_parser("datahub-token", help="Create and save a DataHub access token")
    p_token.add_argument("--username", default="datahub")
    p_token.add_argument("--password", default="datahub")
    sub.add_parser("status", help="Show connection and seed status")
    args = parser.parse_args()

    if args.command == "seed":
        steps = list(STEPS) if args.step == "all" else [args.step]
        return asyncio.run(seed(steps))
    if args.command == "datahub-token":
        return asyncio.run(datahub_token(args.username, args.password))
    return asyncio.run(status())


if __name__ == "__main__":
    sys.exit(main())

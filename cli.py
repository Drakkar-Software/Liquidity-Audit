import argparse
import asyncio
import logging
import pathlib
import sys

import liquidity_audit.application.workflows.daily_run as daily_run_workflow
import liquidity_audit.application.workflows.identify_selected_only as identify_selected_only_workflow
import liquidity_audit.application.workflows.re_evaluate_data as re_evaluate_data_workflow
import liquidity_audit.application.workflows.resolve_websites as resolve_websites_workflow
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.dotenv_loader as dotenv_loader
import liquidity_audit.infrastructure.mattermost_notifier as mattermost_notifier

_LOGGER = logging.getLogger(pathlib.Path(__file__).stem)


class _ShortNameFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        original_name = record.name
        record.name = original_name.rsplit(".", 1)[-1]
        try:
            return super().format(record)
        finally:
            record.name = original_name


def _configure_logging() -> None:
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(_ShortNameFormatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    ))
    logging.basicConfig(level=logging.INFO, handlers=[log_handler])
    logging.getLogger("ccxt").setLevel(logging.WARNING)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Liquidity Audit sync")
    parser.add_argument("--config", required=True, help="Path to JSON config file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run",
        help="Full daily pipeline: discover listings, analyze health, select projects",
    )
    run_parser.add_argument(
        "--identify-only",
        action="store_true",
        help="Discover and save new listings only; skip analysis and selection",
    )

    subparsers.add_parser(
        "re-evaluate-data",
        help="Refresh health metrics from CSV and rebuild analysis JSON from cached raw blocks",
    )

    subparsers.add_parser(
        "identify-selected-only",
        help="Select daily projects from listings.csv and append selected_history.csv",
    )

    subparsers.add_parser(
        "update-websites",
        help="Resolve CoinGecko websites for selection candidates and save to listings.csv",
    )

    return parser


def _parse_args(argv: list[str]) -> argparse.Namespace:
    return _build_parser().parse_args(argv)


async def _dispatch(command: str, args: argparse.Namespace, config: app_config.AppConfig) -> None:
    if command == "run":
        if args.identify_only:
            _LOGGER.info("Identify-only mode enabled")
        run_result = await daily_run_workflow.run(config, identify_only=args.identify_only)
        if run_result is not None:
            await mattermost_notifier.send_run_notifications(
                run_result.run_summary,
                run_result.daily_selections,
            )
        return

    if command == "re-evaluate-data":
        await re_evaluate_data_workflow.run(config)
        return

    if command == "identify-selected-only":
        run_result = await identify_selected_only_workflow.run(config)
        await mattermost_notifier.send_run_notifications(
            run_result.run_summary,
            run_result.daily_selections,
            post=False,
        )
        _LOGGER.info(
            "Identify-selected-only complete: selections_proposed=%s",
            run_result.run_summary.selections_proposed_total,
        )
        return

    if command == "update-websites":
        resolved_count = await resolve_websites_workflow.run(config)
        _LOGGER.info("Update-websites complete: %s listing(s) updated", resolved_count)
        return

    raise ValueError(f"Unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    dotenv_loader.load_project_dotenv()
    _configure_logging()
    try:
        args = _parse_args(argv or sys.argv[1:])
    except SystemExit as error:
        return int(error.code or 2)
    config = app_config.load_config(args.config)
    _LOGGER.info(
        "Config loaded: exchanges=%s, listings_csv=%s",
        config.exchanges,
        config.listings_csv_path,
    )
    try:
        asyncio.run(_dispatch(args.command, args, config))
    except ValueError as error:
        _LOGGER.error("%s", error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

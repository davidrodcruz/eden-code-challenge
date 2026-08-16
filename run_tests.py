import argparse
import sys

from utils.run_tests_utils import run_tests


def main():
    parser = argparse.ArgumentParser(
        description="eden-code-challenge - Web UI Test Framework"
    )
    parser.add_argument(
        "-t", "--team", required=True, help="Team name (comma-separated for multiple)"
    )
    parser.add_argument(
        "-f", "--feature", help="Feature file name (e.g., login.feature)"
    )
    parser.add_argument("--tags", help="Behave tags filter (e.g., @smoke)")
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (overrides team config.yaml)",
    )

    args = parser.parse_args()
    exit_code = run_tests(
        args.team, args.feature, args.tags, args.headless
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

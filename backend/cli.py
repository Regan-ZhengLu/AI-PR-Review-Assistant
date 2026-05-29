"""CLI entrypoint for DiffSense AI MVP."""

from __future__ import annotations

import argparse

from .analyzer import analyze_pr
from .report_formatter import format_markdown_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a GitHub Pull Request with DiffSense AI")
    parser.add_argument("pr_url", help="GitHub Pull Request URL")
    args = parser.parse_args()
    review = analyze_pr(args.pr_url)
    print(format_markdown_report(review))


if __name__ == "__main__":
    main()

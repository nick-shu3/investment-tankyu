#!/usr/bin/env python3
"""Run the research site's pre-publication checks."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*command):
    print('+', *command, flush=True)
    try:
        subprocess.run(command, cwd=ROOT, check=True)
    except FileNotFoundError:
        raise SystemExit(f'Required command not found: {command[0]}')
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--full', action='store_true', help='also build and check the site')
    mode.add_argument('--built-site', action='store_true', help='check an existing _site build')
    args = parser.parse_args()

    if not args.built_site:
        run(sys.executable, 'scripts/validate_publication.py')
        run(sys.executable, 'scripts/validate_articles.py')
    if args.full:
        run('jekyll', 'build', '--destination', '_site')
    if args.full or args.built_site:
        run(sys.executable, 'scripts/check_site.py')
        run('node', 'scripts/check_layout.cjs')


if __name__ == '__main__':
    main()

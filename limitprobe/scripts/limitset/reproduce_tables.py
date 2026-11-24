"""Rebuild results tables offline from a results bundle."""
import argparse
from pathlib import Path
from make_results import build_tables


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('results/limitset_final'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build_tables(args.root)
    args.out.write_text(result, encoding='utf-8')
    print(result, end='')


if __name__ == '__main__':
    main()

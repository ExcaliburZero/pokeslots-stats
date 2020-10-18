from typing import List

import argparse
import sys

import pandas as pd


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    parser_pokemon_info = subparsers.add_parser("pokemon_info", help="lists information on the given pokemon data csv")
    parser_pokemon_info.add_argument("pokemon_csv")

    args = parser.parse_args(argv)

    if args.command == "pokemon_info":
        data = pd.read_csv(args.pokemon_csv)

        print(data.groupby(["rarity"]).describe())
        print(data)

        duplicates = data[data["name"].duplicated() == True]

        if len(duplicates) > 0:
            print()
            print("There are duplicate pokemon entries, these are the 2nd+ entries for each duplicate")
            print(duplicates)
    elif args.command == None:
        parser.print_help()

        sys.exit(1)
    else:
        print("Invalid command:", args.command)
        parser.print_help()

        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
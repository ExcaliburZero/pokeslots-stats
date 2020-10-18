from dataclasses import dataclass
from typing import Any, Dict, IO, List

import argparse
import csv
import json
import sys

import pandas as pd


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    parser_pokemon_info = subparsers.add_parser(
        "pokemon_info", help="lists information on the given pokemon data csv"
    )
    parser_pokemon_info.add_argument("pokemon_csv")

    parser_simulate = subparsers.add_parser("simulate", help="")
    parser_simulate.add_argument("pokemon_csv")
    parser_simulate.add_argument("probabilities_json")

    args = parser.parse_args(argv)

    if args.command == "pokemon_info":
        data = pd.read_csv(args.pokemon_csv)

        print(data.groupby(["rarity"]).describe())
        print(data)

        duplicates = data[data["name"].duplicated() == True]

        if len(duplicates) > 0:
            print()
            print(
                "There are duplicate pokemon entries, these are the 2nd+ entries for each duplicate"
            )
            print(duplicates)
    elif args.command == "simulate":
        with open(args.pokemon_csv) as input_stream:
            pokemon = Pokemon.from_csv(input_stream)

        with open(args.probabilities_json) as input_stream:
            slot_machine = SlotMachine.from_json(json.load(input_stream))

        print(pokemon)
        print(len(pokemon))
        print(slot_machine)
    elif args.command == None:
        parser.print_help()

        sys.exit(1)
    else:
        print("Invalid command:", args.command)
        parser.print_help()

        sys.exit(1)


@dataclass
class Pokemon:
    common_pokemon: List[str]
    uncommon_pokemon: List[str]
    rare_pokemon: List[str]
    very_rare_pokemon: List[str]
    legendary_pokemon: List[str]
    ultra_beast_pokemon: List[str]

    def __len__(self) -> int:
        return sum(
            (
                len(entry)
                for entry in [
                    self.common_pokemon,
                    self.uncommon_pokemon,
                    self.rare_pokemon,
                    self.very_rare_pokemon,
                    self.legendary_pokemon,
                    self.ultra_beast_pokemon,
                ]
            )
        )

    @staticmethod
    def from_csv(input_stream: IO[str]) -> "Pokemon":
        common_pokemon: List[str] = []
        uncommon_pokemon: List[str] = []
        rare_pokemon: List[str] = []
        very_rare_pokemon: List[str] = []
        legendary_pokemon: List[str] = []
        ultra_beast_pokemon: List[str] = []

        reader = csv.DictReader(input_stream)
        for row in reader:
            if row["rarity"] == "Common":
                common_pokemon.append(row["name"])
            elif row["rarity"] == "Uncommon":
                uncommon_pokemon.append(row["name"])
            elif row["rarity"] == "Rare":
                rare_pokemon.append(row["name"])
            elif row["rarity"] == "Very rare":
                very_rare_pokemon.append(row["name"])
            elif row["rarity"] == "Legendary":
                legendary_pokemon.append(row["name"])
            elif row["rarity"] == "Ultra beast":
                ultra_beast_pokemon.append(row["name"])
            else:
                assert False

        return Pokemon(
            common_pokemon,
            uncommon_pokemon,
            rare_pokemon,
            very_rare_pokemon,
            legendary_pokemon,
            ultra_beast_pokemon,
        )


@dataclass
class SlotMachine:
    common_probability: float
    uncommon_probability: float
    rare_probability: float
    very_rare_probability: float
    legendary_probability: float
    ultra_beast_probability: float

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "SlotMachine":
        assert "common_probability" in data
        assert "uncommon_probability" in data
        assert "rare_probability" in data
        assert "very_rare_probability" in data
        assert "legendary_probability" in data
        assert "ultra_beast_probability" in data

        return SlotMachine(
            data["common_probability"],
            data["uncommon_probability"],
            data["rare_probability"],
            data["very_rare_probability"],
            data["legendary_probability"],
            data["ultra_beast_probability"],
        )

    def roll(self, pokemon: Pokemon) -> List[str]:
        pass


if __name__ == "__main__":
    main(sys.argv[1:])
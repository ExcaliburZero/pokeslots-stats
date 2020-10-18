from dataclasses import dataclass, field
from typing import Any, Dict, IO, List

import argparse
import csv
import json
import random
import sys

import pandas as pd
import plotnine as plt9


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
    parser_simulate.add_argument("--rng_seed", type=int, default=42)
    parser_simulate.add_argument("--num_rolls", type=int, default=10)
    parser_simulate.add_argument("--num_cases", type=int, default=1)
    parser_simulate.add_argument(
        "--num_unique_pokemon_plot", default="num_unique_pokemon.png"
    )
    parser_simulate.add_argument("--autorelease", action="store_true", default=False)

    args = parser.parse_args(argv)

    if args.command == "pokemon_info":
        pokemon_info(args)
    elif args.command == "simulate":
        simulate(args)
    elif args.command == None:
        parser.print_help()

        sys.exit(1)
    else:
        print("Invalid command:", args.command)
        parser.print_help()

        sys.exit(1)


def pokemon_info(args: argparse.Namespace) -> None:
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


def simulate(args: argparse.Namespace) -> None:
    random.seed(args.rng_seed)

    with open(args.pokemon_csv) as input_stream:
        pokemon = Pokemon.from_csv(input_stream)

    with open(args.probabilities_json) as input_stream:
        slot_machine = SlotMachine.from_json(json.load(input_stream))

    print(len(pokemon))
    print(slot_machine)

    # Run the simulation
    simulation_data = SimulationData()

    for case_id in range(0, args.num_cases):
        case = simulation_data.new_case(case_id)

        # Note: representing roll credits as 2*num_rolls to avoid floating point issues when
        # accounting for autorelease, which has two released pokemon yield one roll.

        collection = PokemonCollection()
        roll_credits_times_2 = 0
        for i in range(0, args.num_rolls):
            roll_credits_times_2 += 2

            while roll_credits_times_2 >= 2:
                roll_credits_times_2 -= 2

                results = slot_machine.roll(pokemon)
                collection.extend(results)

                if args.autorelease:
                    roll_credits_times_2 += collection.autorelease()

            case.record(pokemon, collection, results)

        print(
            f"{collection.num_unique()} / {len(pokemon)}, ({len(collection.pokemon)})"
        )

    # Output simulation results
    data = simulation_data.to_data_frame()

    plot = (
        plt9.ggplot(data, plt9.aes("roll_num", "num_unique_pokemon", color="case_id"))
        + plt9.geom_line()
        + plt9.geom_hline(yintercept=len(pokemon))
        + plt9.ylim(0, len(pokemon))
    )

    plot.save(args.num_unique_pokemon_plot, dpi=300)
    print("Output:", args.num_unique_pokemon_plot)


@dataclass
class SimulationData:
    cases: Dict[int, "SimulationCase"] = field(default_factory=dict)

    def new_case(self, case_id: int) -> "SimulationCase":
        assert case_id not in self.cases

        case = SimulationCase()
        self.cases[case_id] = case

        return case

    def to_data_frame(self) -> pd.DataFrame:
        sim_results_lists = [
            zip(
                [str(case_id)] * len(simulation_case.num_unique_pokemon),
                range(0, len(simulation_case.num_unique_pokemon)),
                simulation_case.num_unique_pokemon,
            )
            for case_id, simulation_case in self.cases.items()
        ]

        data = pd.DataFrame(
            [item for l in sim_results_lists for item in l],
            columns=["case_id", "roll_num", "num_unique_pokemon"],
        )

        return data


@dataclass
class SimulationCase:
    num_unique_pokemon: List[int] = field(default_factory=list)

    def record(
        self, pokemon: "Pokemon", collection: "PokemonCollection", results: List[str]
    ) -> None:
        self.num_unique_pokemon.append(collection.num_unique())


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
        results: List[str] = []

        data = [
            (self.common_probability, pokemon.common_pokemon),
            (self.uncommon_probability, pokemon.uncommon_pokemon),
            (self.rare_probability, pokemon.rare_pokemon),
            (self.very_rare_probability, pokemon.very_rare_pokemon),
            (self.legendary_probability, pokemon.legendary_pokemon),
            (self.ultra_beast_probability, pokemon.ultra_beast_pokemon),
        ]

        for probability, possible_pokemon in data:
            r = random.random()

            if r <= probability:
                results.append(random.choice(possible_pokemon))

        return results


@dataclass
class PokemonCollection:
    pokemon: Dict[str, int] = field(default_factory=dict)

    def extend(self, new_pokemon: List[str]) -> None:
        for p in new_pokemon:
            if p in self.pokemon:
                self.pokemon[p] += 1
            else:
                self.pokemon[p] = 1

    def num_unique(self) -> int:
        return len(self.pokemon)

    def autorelease(self) -> int:
        num_released = 0
        for name, num in self.pokemon.items():
            if num > 1:
                while num > 1:
                    num -= 1
                    num_released += 1

                self.pokemon[name] = 1

        return num_released


if __name__ == "__main__":
    main(sys.argv[1:])
from dataclasses import dataclass, field
from typing import Any, Callable, cast, Dict, IO, List, Optional, Tuple

import argparse
import csv
import datetime
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

    parser_estimate_stats = subparsers.add_parser("estimate_stats", help="")
    parser_estimate_stats.add_argument("logs_json", nargs="+")
    parser_estimate_stats.add_argument("--mudae_bot_username", default="Mudamaid 23")
    parser_estimate_stats.add_argument(
        "--output_probabilities_json", default="estimated_probabilities.json"
    )

    parser_simulate = subparsers.add_parser("simulate", help="")
    parser_simulate.add_argument("pokemon_csv")
    parser_simulate.add_argument("probabilities_json")
    parser_simulate.add_argument("--rng_seed", type=int, default=42)
    parser_simulate.add_argument("--num_rolls", type=int, default=10)
    parser_simulate.add_argument("--num_cases", type=int, default=1)
    parser_simulate.add_argument(
        "--num_unique_pokemon_plot", default="num_unique_pokemon.png"
    )
    parser_simulate.add_argument(
        "--num_missing_pokemon_plot", default="num_missing_pokemon.png"
    )
    parser_simulate.add_argument("--autorelease", action="store_true", default=False)

    args = parser.parse_args(argv)

    if args.command == "pokemon_info":
        pokemon_info(args)
    elif args.command == "simulate":
        simulate(args)
    elif args.command == "estimate_stats":
        estimate_stats(args)
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


def estimate_stats(args: argparse.Namespace) -> None:
    # Parse the Discord log JSON files and pull out the information we want
    all_results = []
    for log_filepath in args.logs_json:
        with open(log_filepath, "r") as input_stream:
            log_dict = json.load(input_stream)

        assert "messages" in log_dict

        mudae_posts = [
            msg
            for msg in log_dict["messages"]
            if msg["author"]["name"] == args.mudae_bot_username
        ]

        results = [
            PokeslotResult.from_dict(msg)
            for msg in mudae_posts
            if msg["content"].startswith(":") and "pokéduel" not in msg["content"]
        ]
        all_results.extend(results)

    # Sort the results by time to make the data easier to reason about and work with
    all_results.sort(key=lambda pr: pr.timestamp)

    # Calculate and print summary information
    earliest = all_results[0].timestamp
    latest = all_results[-1].timestamp

    print(f"Time range: {earliest}  to  {latest}")

    common_count = sum((1 for r in all_results if r.common_result is not None))
    common_percent = common_count / float(len(all_results))
    uncommon_count = sum((1 for r in all_results if r.uncommon_result is not None))
    uncommon_percent = uncommon_count / float(len(all_results))
    rare_count = sum((1 for r in all_results if r.rare_result is not None))
    rare_percent = rare_count / float(len(all_results))
    very_rare_count = sum((1 for r in all_results if r.very_rare_result is not None))
    very_rare_percent = very_rare_count / float(len(all_results))
    legendary_count = sum((1 for r in all_results if r.legendary_result is not None))
    legendary_percent = legendary_count / float(len(all_results))
    ultra_beast_count = sum(
        (1 for r in all_results if r.ultra_beast_result is not None)
    )
    ultra_beast_percent = ultra_beast_count / float(len(all_results))

    print(f"Common:  \t{common_percent}\t({common_count} / {len(all_results)})")
    print(f"Uncommon:\t{uncommon_percent}\t({uncommon_count} / {len(all_results)})")
    print(f"Rare:    \t{rare_percent}\t({rare_count} / {len(all_results)})")
    print(f"Very rare:\t{very_rare_percent}\t({very_rare_count} / {len(all_results)})")
    print(f"Legendary:\t{legendary_percent}\t({legendary_count} / {len(all_results)})")
    print(
        f"Ultra beast:\t{ultra_beast_percent}\t({ultra_beast_count} / {len(all_results)})"
    )

    common_shiny_count, common_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.common_result
    )
    uncommon_shiny_count, uncommon_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.uncommon_result
    )
    rare_shiny_count, rare_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.rare_result
    )
    very_rare_shiny_count, very_rare_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.very_rare_result
    )
    legendary_shiny_count, legendary_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.legendary_result
    )
    ultra_beast_shiny_count, ultra_beast_shiny_percent = calc_shiny_count_and_rate(
        all_results, lambda r: r.ultra_beast_result
    )

    print("\nShiny rates")

    print(
        f"Common:   \t{common_shiny_percent}\t({common_shiny_count} / {common_count})"
    )
    print(
        f"Uncommon: \t{uncommon_shiny_percent}\t({uncommon_shiny_count} / {uncommon_count})"
    )
    print(f"Rare:     \t{rare_shiny_percent}\t({rare_shiny_count} / {rare_count})")
    print(
        f"Very rare:\t{very_rare_shiny_percent}\t({very_rare_shiny_count} / {very_rare_count})"
    )
    print(
        f"Legendary:\t{legendary_shiny_percent}\t({legendary_shiny_count} / {legendary_count})"
    )
    print(
        f"Ultra beast:\t{ultra_beast_shiny_percent}\t({ultra_beast_shiny_count} / {ultra_beast_count})"
    )

    # Output results to a data file
    slot_machine = SlotMachine(
        common_percent,
        uncommon_percent,
        rare_percent,
        very_rare_percent,
        legendary_percent,
        ultra_beast_percent,
    )

    with open(args.output_probabilities_json, "w") as output_stream:
        slot_machine.write_json(output_stream)

    print("Wrote estimated rarity probabilities to:", args.output_probabilities_json)


def calc_shiny_count_and_rate(
    results: List["PokeslotResult"], get: Callable[["PokeslotResult"], Optional[str]]
) -> Tuple[int, float]:
    count = sum((1 for r in results if get(r) is not None))
    shiny_count = sum(
        (1 for r in results if get(r) is not None and "S" in cast(str, get(r)))
    )
    shiny_percent = shiny_count / float(count) if count > 0 else 0.0

    return shiny_count, shiny_percent


@dataclass
class PokeslotResult:
    timestamp: datetime.datetime
    common_result: Optional[str]
    uncommon_result: Optional[str]
    rare_result: Optional[str]
    very_rare_result: Optional[str]
    legendary_result: Optional[str]
    ultra_beast_result: Optional[str]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PokeslotResult":
        timestamp = PokeslotResult.parse_timestamp(data["timestamp"])

        content = data["content"]
        lines = content.split("\n")

        assert len(lines) in [5, 6]

        common_result = PokeslotResult.parse_result_line(lines[0])
        uncommon_result = PokeslotResult.parse_result_line(lines[1])
        rare_result = PokeslotResult.parse_result_line(lines[2])
        very_rare_result = PokeslotResult.parse_result_line(lines[3])
        legendary_result = PokeslotResult.parse_result_line(lines[4])

        if len(lines) == 6:
            ultra_beast_result = PokeslotResult.parse_result_line(lines[5])
        else:
            ultra_beast_result = None

        return PokeslotResult(
            timestamp,
            common_result,
            uncommon_result,
            rare_result,
            very_rare_result,
            legendary_result,
            ultra_beast_result,
        )

    @staticmethod
    def parse_result_line(line: str) -> Optional[str]:
        if (
            line.endswith("\U0001f514")
            or line.endswith(":wormholebell:")
            or line.endswith(":shinySparkles:")
        ):
            pokemon_name = line.split(":")[1]

            return pokemon_name
        else:
            return None

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime.datetime:
        # 2020-08-11T05:14:14.292+00:00
        timestamp_format = "%Y-%m-%dT%H:%M:%S"

        return datetime.datetime.strptime(timestamp_str[:19], timestamp_format)


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

    num_unique_pokemon_plot = (
        plt9.ggplot(data, plt9.aes("roll_num", "num_unique_pokemon", color="case_id"))
        + plt9.geom_line()
        + plt9.geom_hline(yintercept=len(pokemon))
        + plt9.ylim(0, len(pokemon))
    )

    num_unique_pokemon_plot.save(args.num_unique_pokemon_plot, dpi=300)
    print("Output:", args.num_unique_pokemon_plot)

    data_2 = simulation_data.to_num_missing_data_frame()

    num_missing_pokemon_plot = (
        plt9.ggplot(
            data_2[data_2["case_id"] == 0],
            plt9.aes("roll_num", "num_missing", fill="rarity"),
        )
        + plt9.geom_area()
        + plt9.geom_hline(yintercept=len(pokemon))
        + plt9.ylim(0, len(pokemon))
        + plt9.scale_fill_hue(
            labels=[
                "Common",
                "Uncommon",
                "Rare",
                "Very rare",
                "Legendary",
                "Ultra beast",
            ]
        )
    )

    num_missing_pokemon_plot.save(args.num_missing_pokemon_plot, dpi=300)
    print("Output:", args.num_missing_pokemon_plot)


@dataclass
class SimulationData:
    cases: Dict[int, "SimulationCase"] = field(default_factory=dict)

    def new_case(self, case_id: int) -> "SimulationCase":
        assert case_id not in self.cases

        case = SimulationCase()
        self.cases[case_id] = case

        return case

    def to_num_missing_data_frame(self) -> pd.DataFrame:
        sim_results_lists = [
            (case_id, roll_num, rarity, num_missing)
            for case_id, simulation_case in self.cases.items()
            for roll_num, entries in enumerate(simulation_case.num_missing_by_rarity)
            for rarity, num_missing in entries.items()
        ]

        data = pd.DataFrame(
            sim_results_lists,
            columns=["case_id", "roll_num", "rarity", "num_missing"],
        )

        data["rarity"] = pd.Categorical(
            data["rarity"],
            categories=[
                "Common",
                "Uncommon",
                "Rare",
                "Very rare",
                "Legendary",
                "Ultra beast",
            ],
            ordered=True,
        )

        return data

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
    num_missing_by_rarity: List[Dict[str, int]] = field(default_factory=list)

    def record(
        self, pokemon: "Pokemon", collection: "PokemonCollection", results: List[str]
    ) -> None:
        self.num_unique_pokemon.append(collection.num_unique())
        self.num_missing_by_rarity.append(collection.num_missing_by_rarity(pokemon))


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

    def write_json(self, output_stream: IO[str]) -> None:
        data = {
            "common_probability": self.common_probability,
            "uncommon_probability": self.uncommon_probability,
            "rare_probability": self.rare_probability,
            "very_rare_probability": self.very_rare_probability,
            "legendary_probability": self.legendary_probability,
            "ultra_beast_probability": self.ultra_beast_probability,
        }

        json.dump(data, output_stream, indent=4)

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

    def num_missing_by_rarity(self, pokemon: Pokemon) -> Dict[str, int]:
        entries = [
            ("Common", pokemon.common_pokemon),
            ("Uncommon", pokemon.uncommon_pokemon),
            ("Rare", pokemon.rare_pokemon),
            ("Very rare", pokemon.very_rare_pokemon),
            ("Legendary", pokemon.legendary_pokemon),
            ("Ultra beast", pokemon.ultra_beast_pokemon),
        ]

        non_owned_pokemon_by_rarity: Dict[str, List[str]] = {}
        for rarity_name, pokemon_in_rarity in entries:
            non_owned_pokemon: List[str] = []
            for p in pokemon_in_rarity:
                if p not in self.pokemon:
                    non_owned_pokemon.append(p)

            non_owned_pokemon_by_rarity[rarity_name] = non_owned_pokemon

        return {r: len(p) for r, p in non_owned_pokemon_by_rarity.items()}

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
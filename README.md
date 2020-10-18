## Pokeslots Stats
This is a script that calculates some statistical information about the [Pokeslots](https://mudae.fandom.com/wiki/Pokéslot) feature of the Discord bot Mudae.

## Usage
### `pokemon_info`
```
$ python pokeslots-stats/__main__.py pokemon_info data/pokemon.csv
             name                       
            count unique        top freq
rarity                                  
Common        145    145     Spoink    1
Legendary      67     67   Landorus    1
Rare          275    275     Togepi    1
Ultra beast    11     11  Xurkitree    1
Uncommon      187    187    Kingler    1
Very rare     124    124   Blaziken    1
            name       rarity
0       Caterpie       Common
1         Weedle       Common
2         Pidgey       Common
3        Rattata       Common
4        Spearow       Common
..           ...          ...
804     Guzzlord  Ultra beast
805      Poipole  Ultra beast
806    Naganadel  Ultra beast
807    Stakataka  Ultra beast
808  Blacephalon  Ultra beast

[809 rows x 2 columns]
```

## Development notes

### Create environment
```bash
conda create -f pokeslots-stats.yml
```

### Update environment
```bash
conda env update -f pokeslots-stats.yml
```
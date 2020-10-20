## Pokeslots Stats
This is a script that calculates some statistical information about the [Pokeslots](https://mudae.fandom.com/wiki/Pokéslot) feature of the Discord bot Mudae.

## Usage
### pokemon_info
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

### simulate
```
$ python pokeslots-stats/__main__.py simulate data/pokemon.csv estimated_probabilities.json --num_rolls 500 --num_cases 10 --autorelease
809
SlotMachine(common_probability=0.8977164605137964, uncommon_probability=0.18934348239771645, rare_probability=0.056612749762131306, very_rare_probability=0.027117031398667935, legendary_probability=0.0019029495718363464, ultra_beast_probability=0.0009514747859181732)
316 / 809, (316)
323 / 809, (323)
330 / 809, (330)
340 / 809, (340)
306 / 809, (306)
308 / 809, (308)
309 / 809, (309)
311 / 809, (311)
318 / 809, (318)
322 / 809, (322)
/home/chris/anaconda3/envs/pokeslots-stats/lib/python3.8/site-packages/plotnine/ggplot.py:727: PlotnineWarning: Saving 6.4 x 4.8 in image.
/home/chris/anaconda3/envs/pokeslots-stats/lib/python3.8/site-packages/plotnine/ggplot.py:730: PlotnineWarning: Filename: num_unique_pokemon.png
Output: num_unique_pokemon.png
/home/chris/anaconda3/envs/pokeslots-stats/lib/python3.8/site-packages/plotnine/ggplot.py:727: PlotnineWarning: Saving 6.4 x 4.8 in image.
/home/chris/anaconda3/envs/pokeslots-stats/lib/python3.8/site-packages/plotnine/ggplot.py:730: PlotnineWarning: Filename: num_missing_pokemon.png
Output: num_missing_pokemon.png
```

### estimate_stats
```
$ python pokeslots-stats/__main__.py estimate_stats "server - channel*.json"
Time range: 2020-08-11 05:14:22  to  2020-10-19 06:35:34
Common:  	0.8977164605137964	(1887 / 2102)
Uncommon:	0.18934348239771645	(398 / 2102)
Rare:    	0.056612749762131306	(119 / 2102)
Very rare:	0.027117031398667935	(57 / 2102)
Legendary:	0.0019029495718363464	(4 / 2102)
Ultra beast:	0.0009514747859181732	(2 / 2102)
Wrote estimated rarity probabilities to: estimated_probabilities.json
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

### Testing
```bash
make test
```
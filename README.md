# lol-stats
collect player stats from Riot's League of Legends API and determine win rates as, with and against each champion

## Intro

lol-stats uses [RiotWatcher](https://github.com/pseudonym117/Riot-Watcher) to interact with [Riot's League of Legends API](https://developer.riotgames.com/apis) to get a player's matchlist. This list is then used to pull each individual game and game timeline from the database. Desired stats can then be extracted from each game and collected to determine winrates when playing as, with and against each champion. The classic question of 'Is enemy Yasuo really better than ally Yasuo?' is also answered by comparing winrates for each champion when on allied vs opposing team. Two-tailed p-values are also calculated, and stastically significant entries are highlighted. A plot of game durations can be generated, and this data can then be split to consider only forfeit or non-forfeit games.

To use this tool for other accounts, an API key from Riot's website is needed.

The main function (via show_all_features) provides a demonstation of key featues and by default saves the downloaded matchlist, matches and timelines as three jsons. Accounts tested generally have ~2000 games accessible, leading to file sizes of ~.3 MB, ~60 MB and ~230 MB. Due to API rate limitting, requesting all of these files takes ~1.5 hour.

The program can be called from the command line as follows, and if the source provided internally is set to api, the program prompts for a valid username. If an invalid name is provided, the program quits.

Unfortunately, diving deeper into the stats currently requires an interactive environment (IPython etc.), but this will hopefully become an interactive web app one day!

## Sample data output for my account

Output from my account (vayneofcastamere) is accessible in the output folder--output.txt is copied from terminal when run, and graphs that pop up when run are likewise included.

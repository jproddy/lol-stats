# lol-stats
collect player stats from Riot's League of Legends API and determine win rates as, with and against each champion

## Intro

lol-stats uses [RiotWatcher](https://github.com/pseudonym117/Riot-Watcher) to interact with [Riot's League of Legends API](https://developer.riotgames.com/apis) to get a player's matchlist. This list is then used to pull each individual game from the database. Desired stats can then be extracted from each game and collected to determine winrates when playing as, with and against each champion.

To use this tool, an API key from Riot's website is needed.

The main function provides a demonstation of key featues and by default saves the downloaded matchlist and matches as jsons. Accounts tested generally have ~2000 games accessible, leading to file sizes of ~.2 MB and ~60 MB. Due to API rate limitting, requesting all of these files takes ~1 hour.

The program can be called from the command line with your account name as an argument:

    python lol-stats.py vayneofcastamere
  
It hasn't been properly protected from invalid inputs, but should work if supplied with a valid account name. This will be fixed soon.

Unfortunately, diving deeper into the stats currently requires an interactive environment (IPython etc.), but this will hopefully become an interactive web app one day!

## Sample data output for my account

Output is accessible in output.txt as copied from terminal when run.

# beets-titlecase
Provides helper functions to convert a library to Title Case. Also provides some other useful helper functions to fix and normalize tags.

## Commands
```
$ beet titlecase
```
Converts every tag to Title Case. Please make sure that this is what you prefer before using this command. If you want to go back, you will need to reimport your files again to reset the tags.

```
$ beet mixfixer
```
This command does a few things:
- Removes "(Original Mix)" text from song titles, case insensitive.
- Converts brackets [ and ] to parentheses ( and )
- Converts Spotify style tags with the text " - Radio Edit" to "(Radio Edit)"
- Converts Spotify style tags with the text " - Extended Mix" to "(Extended Mix)"

```
$ beet quotefixer
```
Replaces all instances of the ’ character with ' (since many users do not have ’ on their keyboard)

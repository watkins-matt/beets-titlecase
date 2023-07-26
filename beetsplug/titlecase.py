import re

from beets import dbcore
from beets.plugins import BeetsPlugin
from beets.ui import Subcommand


def to_title(string):
    return re.sub(
        r"(\s[\W]*|^[\W]*)([a-z])?",
        lambda m: m.group(1) + safe_title(m.group(2)),
        string,
    )


def safe_title(string):
    return string.title() if string is not None else ""


def _titlecase(text):
    if text:
        return to_title(text)
    else:
        return ""


class TitleCasePlugin(BeetsPlugin):
    def commands(self):
        titlecase = Subcommand("titlecase", help="Converts everything to Title Case.")
        titlecase.func = self.titlecase  # type: ignore

        mixfixer = Subcommand("mixfixer", help="Fixes issues with mix titles.")
        mixfixer.func = self.mix_fixer  # type: ignore

        quotefixer = Subcommand(
            "quotefixer", help="Changes MusicBrainz style ’ to regular ' marks."
        )
        quotefixer.func = self.quote_fixer  # type: ignore

        # Add template function titlecase
        self.template_funcs["titlecase"] = _titlecase  # type: ignore

        # Add import hook to convert everything to titlecase
        # TODO: This should be an option
        self.import_stages = [self.import_stage_fixer]

        # self.register_listener("trackinfo_received", self.trackinfo_received)
        self.register_listener("albuminfo_received", self.trackinfo_received)
        return [titlecase, mixfixer, quotefixer]

    # Receives beets.autotag.hooks.AlbumInfo or TrackInfo
    def trackinfo_received(self, info):
        self.album_info_fix_quotes(info)
        self.album_info_to_titlecase(info)

    def album_info_fix_quotes(self, info):
        info.artist = info.artist.replace("’", "'")
        info.album = info.album.replace("’", "'")
        info.artist_sort = info.artist_sort.replace("’", "'")
        info.artist_credit = info.artist_credit.replace("’", "'")

        tracks = info.tracks
        for track in tracks:
            track.title = track.title.replace("’", "'")
            track.artist = track.artist.replace("’", "'")
            track.artist_sort = track.artist_sort.replace("’", "'")
            track.artist_credit = track.artist_credit.replace("’", "'")

    def album_info_to_titlecase(self, info):
        info.artist = to_title(info.artist)
        info.album = to_title(info.album)
        info.artist_sort = to_title(info.artist_sort)
        info.artist_credit = to_title(info.artist_credit)

        tracks = info.tracks
        for track in tracks:
            track.title = to_title(track.title)
            track.artist = to_title(track.artist)
            track.artist_sort = to_title(track.artist_sort)
            track.artist_credit = to_title(track.artist_credit)

    def import_stage_fixer(self, session, task):
        for song in task.imported_items():
            self.song_to_titlecase(song)
            self.song_convert_brackets(song)
            self.song_fix_extended_mix(song)
            self.song_remove_original_mix(song)
            self.song_fix_radio_edit(song)

    def quote_fixer(self, lib, opts, args):
        total = 0
        fields = [
            "title",
            "artist",
            "album",
            "artist_credit",
            "artist_sort",
            "albumartist",
            "albumartist_credit",
            "albumartist_sort",
        ]

        for field in fields:
            self._log.info("Checking {0} field...", field)
            query = dbcore.query.RegexpQuery(field, r"\’")
            songs = lib.items(query)
            total += len(songs)

            for song in songs:
                self.song_fix_quotes(song, field)

        self._log.info("Updated {0} items.", total)

    def mix_fixer(self, lib, opts, args):
        # Remove original mix from everything
        query = dbcore.query.RegexpQuery("title", r" \([Oo]riginal [Mm]ix\)")
        songs = lib.items(query)
        total = len(songs)

        for song in songs:
            self.song_remove_original_mix(song)

        # Convert brackets to parentheses
        query = dbcore.query.RegexpQuery("title", r"(\[|\])")
        songs = songs = lib.items(query)
        total += len(songs)

        for song in songs:
            self.song_convert_brackets(song)

        # Fix radio edit
        query = dbcore.query.RegexpQuery("title", " - [Rr]adio [Ee]dit")
        songs = songs = lib.items(query)
        total += len(songs)

        for song in songs:
            self.song_fix_radio_edit(song)

        # Fix extended mix
        query = dbcore.query.RegexpQuery("title", " - [Ee]xtended [Mm]ix")
        songs = songs = lib.items(query)
        total += len(songs)

        for song in songs:
            self.song_fix_extended_mix(song)

        self._log.info("Updated {0} items.", total)

    def titlecase_field(self, lib, field_name):
        query = dbcore.query.RegexpQuery(field_name, r"(\s[\W]*|^[\W]*)([a-z])+")
        songs = lib.items(query)
        total = 0

        for song in songs:
            total += self.song_to_titlecase(song)

        return total

    def titlecase(self, lib, opts, args):
        fields = ["title", "album", "artist", "albumartist"]
        total = 0

        for field in fields:
            self._log.info("Checking {0} field...", field)
            total += self.titlecase_field(lib, field)

        self._log.info("Updated {0} items.", total)

    def song_to_titlecase(self, song):
        total = 0
        fields = ["title", "album", "artist", "albumartist"]

        # Iterate through each field in the song
        for field in fields:
            original = song[field]
            capitalized = to_title(original)

            # Only capitalize the field if it needs it
            if capitalized != original:
                self._log.info("{0} -> {1}", original, capitalized)
                song[field] = capitalized
                total += 1

        # Store back in the database
        song.store()
        song.write()
        return total

    def song_fix_quotes(self, song, field_name="title"):
        field_value = song[field_name]
        fixed_value = field_value.replace("’", "'")

        self._log.info("{0} -> {1}", field_value, fixed_value)
        song[field_name] = fixed_value

        song.store()
        song.write()

    def song_remove_original_mix(self, song):
        title = song["title"]
        fixed = to_title(title).replace(" (Original Mix)", "")

        self._log.info("{0} -> {1}", title, fixed)
        song["title"] = fixed

        song.store()
        song.write()

    def song_convert_brackets(self, song):
        title = song["title"]
        fixed = title.replace("[", "(").replace("]", ")")

        self._log.info("{0} -> {1}", title, fixed)
        song["title"] = fixed

        song.store()
        song.write()

    def song_fix_radio_edit(self, song):
        title = song["title"]
        fixed = to_title(title)
        fixed = fixed.replace(" - Radio Edit", " (Radio Edit)")

        self._log.info("{0} -> {1}", title, fixed)
        song["title"] = fixed

        song.store()
        song.write()

    def song_fix_extended_mix(self, song):
        title = song["title"]
        fixed = to_title(title)
        fixed = fixed.replace(" - Extended Mix", " (Extended Mix)")

        self._log.info("{0} -> {1}", title, fixed)
        song["title"] = fixed

        song.store()
        song.write()

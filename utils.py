
class Utilities:

    @classmethod
    def format_site_speaker_name(cls, speaker_name: str) -> str:
        # TODO: extend list of strings to remove from speaker

        _strings_to_remove = [
            "Dr.",
            "Mrs.",
        ]
        #remove unwanted titles from speaker names

        for string in _strings_to_remove:
            speaker_name = speaker_name.replace(string, "")

        # remove extraneous spaces
        speaker_name = speaker_name.strip()
        return speaker_name

    @classmethod
    def format_site_title(cls, site_title: str) -> str:
        return site_title

    @classmethod
    def format_site_series_number(cls, site_series_number: str) -> str:
        """Formats the site series number from format: 'Part XXX of a YYY part series.' to 'XX/YY"""
        parts = site_series_number.split()
        formatted_series_number = f"{parts[1].rjust(2, '0')}/{parts[4].rjust(2, '0')}"
        return formatted_series_number

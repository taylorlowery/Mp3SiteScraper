from dataclasses import is_dataclass, fields


class Utilities:

    @classmethod
    def format_site_speaker_name(cls, speaker_name: str) -> str:
        """Remove unwanted titles, extra spaces, and other strings from speaker names"""
        # TODO: extend list of strings to remove from speaker

        _strings_to_remove = [
            "Dr.",
            "Mrs.",
            "Mr.",
            "Rev.",
            "Pastor",
            "Ms.",
            "Dr ",
            "Mrs ",
            "Mr ",
            "Rev "            
        ]
        for string in _strings_to_remove:
            speaker_name = speaker_name.replace(string, "")

        # remove extra spaces
        speaker_name = speaker_name.strip()
        return speaker_name

    @classmethod
    def format_site_title(cls, site_title: str) -> str:
        """Remove unwanted symbols from site titles"""
        # remove double quotes
        site_title = site_title.replace('""', '')
        return site_title

    @classmethod
    def format_site_series_number(cls, site_series_number: str) -> str:
        """Formats the site series number from format: 'Part XXX of a YYY part series.' to 'XX/YY"""
        parts = site_series_number.split()
        formatted_series_number = f"{parts[1].rjust(2, '0')}/{parts[4].rjust(2, '0')}"
        return formatted_series_number

    @classmethod
    def clean_html_contents(cls, html_element):
        if html_element is None:
            return ""
        return cls.remove_extra_whitespace(html_element.text)

    @classmethod
    def remove_extra_whitespace(cls, input: str) -> str:
        return " ".join(input.split())

    @classmethod
    def clean_dataclass_string_fields(cls, instance):
        if not is_dataclass(instance):
            return instance
        for field in [f.name for f in fields(instance)]:
            current_val = getattr(instance, field)
            if isinstance(current_val, str):
                clean_val = cls.remove_extra_whitespace(current_val)
                setattr(instance, field, clean_val)
        return instance

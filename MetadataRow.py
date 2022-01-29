from dataclasses import dataclass
from datetime import datetime


@dataclass
class SiteMetadata:
    # represents metadata gathered from webpage
    site_ID: int = None
    site_Topic: str = ''
    site_Speaker: str = ''
    site_speaker_formatted: str = ''
    site_Title: str = ''
    site_title_formatted: str = ''
    site_SeriesNumber: str = ''
    site_series_number_formatted: str = ''
    site_Organization: str = ''
    site_Ministry: str = ''
    site_Groups: str = ''
    site_Price: str = ''
    site_Description: str = ''
    site_Date: datetime = None,
    site_Type: str = '',
    site_group_first: str = ''
    site_group_smallest: str = ''
    site_group_matched: str = ''
    site_details_url: str = ''
    site_download_url: str = ''
    site_outline_url: str = ''
    site_speaker_id: int = None
    site_speaker_url: str = ''
    site_speaker_image_url: str = ''


@dataclass
class FileData:
    # represents metadata gathered from mp3 file
    file_filename_original: str = ''
    file_filename_current: str = ''
    file_download_path: str = ''
    file_download_success: bool = False
    file_download_last_attempt: datetime = datetime.now()
    file_ext: str = ''
    file_size: int = None
    file_Title: str = ''
    file_Album: str = ''
    file_Album_Artist: str = ''
    file_Artist: str = ''
    file_Genre: str = ''
    file_Track: int = None
    file_Comment: str = ''
    file_Year: str = ''
    file_Composer: str = ''
    file_Artist_Original: str = ''
    file_Title_Original: str = ''
    file_Involved_people: str = ''
    file_Publisher: str = ''


@dataclass
class MiscellaneousMetadata:
    total_tracks: int = None
    album_image_url: str = ''
    details_url: str = ''
    has_outline: bool = False
    notes: str = ''


# Metadata for audio file pulled from web page
@dataclass
class MetadataRow(SiteMetadata, FileData, MiscellaneousMetadata):
    pass

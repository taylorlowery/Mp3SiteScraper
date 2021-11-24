from dataclasses import dataclass
from datetime import datetime


# Metadata for audio file pulled from web page
@dataclass
class AudioFileData:
    id: int = None
    title: str = ''
    album: str = ''
    album_artist: str = ''
    artist: str = ''
    genre: str = ''
    description: str = ''
    track_num: int = None
    total_tracks: int = None
    speaker_image_url: str = ''
    album_image_url: str = ''
    details_url: str = ''
    download_url: str = ''
    comment: str = ''
    year: int = None
    download_successful: bool = False
    last_download_attempt: datetime = datetime.now()

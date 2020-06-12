from datetime import datetime


# Metadata for audio file pulled from web page
class AudioFileData:

    def __init__(self,
                 id=None,
                 title='',
                 album='',
                 album_artist='',
                 artist='',
                 genre='',
                 description='',
                 track_num=None,
                 total_tracks=None,
                 speaker_image_url='',
                 album_image_url='',
                 details_url='',
                 download_url='',
                 comment='',
                 year=None,
                 download_successful=False,
                 last_download_attempt=datetime.now()):
        self.id = id
        self.title = title
        self.album = album
        self.album_artist = album_artist
        self.artist = artist
        self.genre = genre
        self.description = description
        self.track_num = track_num
        self.total_tracks = total_tracks
        self.speaker_image_url = speaker_image_url
        self.album_image_url = album_image_url
        self.details_url = details_url
        self.download_url = download_url
        self.comment = comment
        self.year = year
        self.download_successful = download_successful
        self.last_download_attempt = last_download_attempt



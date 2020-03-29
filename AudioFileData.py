from datetime import  datetime


# Metadata for audio file pulled from web page
class AudioFileData:

    def __init__(self):
        self.id = None
        self.title = ''
        self.album = ''
        self.album_artist = ''
        self.artist = ''
        self.genre = ''
        self.description = ''
        self.track_num = None
        self.total_tracks = None
        self.speaker_image_url = ''
        self.album_image_url = ''
        self.details_url = ''
        self.download_url = ''
        self.comment = ''
        self.year = None
        self.download_successful = False
        self.last_download_attempt = datetime.now()


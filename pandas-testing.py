import pandas as pd

from AudioFileData import AudioFileData

df = pd.read_csv('files.csv')

# dataframe to audiofiles
listOfFiles = [(AudioFileData(id=row.id,
                              title=row.title,
                              album=row.album,
                              album_artist=row.album_artist,
                              artist=row.artist,
                              genre=row.genre,
                              description=row.description,
                              track_num=row.track_num,
                              total_tracks=row.total_tracks,
                              speaker_image_url=row.speaker_image_url,
                              album_image_url=row.album_image_url,
                              details_url=row.details_url,
                              download_url=row.download_url,
                              comment=row.comment,
                              year=row.year,
                              download_successful=row.download_successful,
                              last_download_attempt=row.last_download_attempt)) for i, row in df.iterrows()]

for file in listOfFiles:
    file.id = 80085

# audiofiles to dataframe
otherfields = dir(listOfFiles[0])
fields = vars(listOfFiles[0]).keys()
dataframe = pd.DataFrame([[getattr(i, j) for j in fields] for i in listOfFiles], columns=fields)

# dataframe to csv
dataframe.to_csv('metadata.csv', index=False)

# dataframe to sqlite


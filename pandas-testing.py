import pandas as pd

from MetadataRow import MetadataRow

df = pd.read_csv('files.csv')

# dataframe to audiofiles
listOfFiles = [(MetadataRow(id=row.site_ID,
                            title=row.site_Title,
                            album=row.file_Album,
                            album_artist=row.file_Album_Artist,
                            artist=row.file_Artist,
                            genre=row.file_Genre,
                            description=row.site_Description,
                            track_num=row.file_Track,
                            total_tracks=row.total_tracks,
                            speaker_image_url=row.site_speaker_image_url,
                            album_image_url=row.album_image_url,
                            details_url=row.details_url,
                            download_url=row.site_download_url,
                            comment=row.file_Comment,
                            year=row.file_Year,
                            download_successful=row.file_download_success,
                            last_download_attempt=row.file_download_last_attempt)) for i, row in df.iterrows()]

for file in listOfFiles:
    file.site_ID = 80085

# audiofiles to dataframe
otherfields = dir(listOfFiles[0])
fields = vars(listOfFiles[0]).keys()
dataframe = pd.DataFrame([[getattr(i, j) for j in fields] for i in listOfFiles], columns=fields)

# dataframe to csv
dataframe.to_csv('metadata.csv', index=False)

# dataframe to sqlite


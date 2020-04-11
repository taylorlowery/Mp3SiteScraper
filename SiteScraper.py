from bs4 import BeautifulSoup
import requests
import eyed3
import urllib.request
import io
from PIL import Image
import csv
import os
import shutil
import pandas as pd

import credentials
import settings

from AudioFileData import AudioFileData

# use constants from settings page
STORAGE_PATH = settings.STORAGE_PATH
SITE_URL = settings.SITE_URL
CSV_OUTPUT_FILE = settings.CSV_OUTPUT_PATH

# use credentials from credentials page
USERNAME = credentials.USERNAME
PASSWORD = credentials.PASSWORD


def clean_html_contents(html_element):
    if html_element is None:
        return ''
    return html_element.text.replace('\r', '').replace('\n', '').strip()


def generate_login_data(login_page):
    login_data = {
        'ctl00$ContentPlaceHolder$txtEmailAddress': USERNAME,
        'ctl00$ContentPlaceHolder$txtPassword': PASSWORD
    }
    login_soup = BeautifulSoup(login_page.content, 'lxml')

    # add params from form to login data
    login_data["__EVENTARGUMENT"] = login_soup.select_one('#__EVENTARGUMENT')
    login_data["__EVENTTARGET"] = login_soup.select_one('#__EVENTTARGET')
    login_data["__VIEWSTATE"] = login_soup.select_one("#__VIEWSTATE")["value"]
    login_data["__VIEWSTATEGENERATOR"] = login_soup.select_one('#__VIEWSTATEGENERATOR')["value"]
    login_data["__EVENTVALIDATION"] = login_soup.select_one('#__EVENTVALIDATION')["value"]
    login_data["ct100$txtSearchText"] = None
    login_data['ctl00$ContentPlaceHolder$cmdLogin'] = 'Log In'
    login_data['ctl00$txtEmailAddress'] = None
    login_data['ctl00$vcerevtxtEmailAddress_ClientState'] = None
    login_data['ctl00$wmetxtEmailAddress_ClientState'] = None
    return login_data


def audio_file_to_dict(file):
    audio_file_dict = {'Id': file.id,
                       'Title': file.title,
                       'Album': file.album,
                       'Album Artist': file.album_artist,
                       'Artist': file.artist,
                       'Genre': file.genre,
                       'Description': file.description,
                       'Track': file.track_num,
                       'Total Tracks': file.total_tracks,
                       'Speaker Image URL': file.speaker_image_url,
                       'Album Image URL': file.album_image_url,
                       'Details URL': file.details_url,
                       'Download URL': file.download_url,
                       'Comment': file.comment,
                       'Download Successful': file.download_successful,
                       'Last Download Attempt': file.last_download_attempt}
    return audio_file_dict

# TODO: replace csv with pandas, which can
def save_files_to_csv(files, overwrite=False):
    with open(CSV_OUTPUT_FILE, 'w+') as f:
        with open('temp_files.csv', 'w+') as t:

            header_names = ['Id',
                            'Title',
                            'Album',
                            'Album Artist',
                            'Artist',
                            'Genre',
                            'Description',
                            'Track',
                            'Total Tracks',
                            'Speaker Image URL',
                            'Album Image URL',
                            'Details URL',
                            'Download URL',
                            'Comment',
                            'Download Successful',
                            'Last Download Attempt']

            writer = csv.DictWriter(t, fieldnames=header_names)
            reader = csv.DictReader(f, fieldnames=header_names)

            audio_files = [file['audio_file_data'] for file in files]

            rowCount = 0
            # only runs if there are already rows in csv
            for row in reader:
                rowCount = rowCount + 1
                needs_update = False
                update_row = None
                for file in files:
                    if row['Id'] == file['Id']:
                        needs_update = True
                        update_row = audio_file_to_dict(file)
                        break
                if needs_update:
                    writer.writerow(update_row)
                else:
                    writer.writerow(row)

            # write a new csv
            if rowCount == 0:
                writer.writeheader()
                audio_file_dict = [audio_file_to_dict(file) for file in audio_files]
                writer.writerows(audio_file_dict)

    shutil.copy('temp_files.csv', CSV_OUTPUT_FILE)

   # os.remove('temp_file.py')


def get_file_data_from_page(session, details_url, download_url):
    open_details_page = session.get(details_url)
    details_soup = BeautifulSoup(open_details_page.content, 'lxml')

    # get metadata from page
    content = details_soup.find('td', class_='content')

    audio_file_data = AudioFileData()

    # Title = Title
    audio_file_data.title = clean_html_contents(content.h1) if content.h1 else ''

    if audio_file_data.title == 'Item Details':
        # Error Message - typically to indicate that there is no file at that ID
        warning = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_Notification1_panelNotification'))
        if warning != '':
            audio_file_data.title = warning

    # Album = Organization
    audio_file_data.album = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypOrganization'))
    # Album Artist = Group/Ministry
    audio_file_data.album_artist = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelProductGroups'))
    # Artist = Speaker
    audio_file_data.artist = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypSpeaker'))
    # Genre = Topic
    audio_file_data.genre = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypTopic'))
    # Comment = Description + Speaker
    # page_data['comment'] = content.find(id='').text
    # Description
    audio_file_data.description = content.p.text if content.p else ''
    # Track  # = Series (have to parse because it's formatted as Part x of a y part series.
    # You can see how I did it in the spreadsheet)
    raw_track_info = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'))
    track_data = [x for x in raw_track_info.split() if x.isdigit()] if raw_track_info else ''
    audio_file_data.track_num = track_data[0] if len(track_data) == 2 else None
    audio_file_data.total_tracks = track_data[1] if len(track_data) == 2 else None
    # Year / Date = Unfortunately, no consistent date found on web page. Have to get it from the file

    # image urls
    speaker_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgSpeaker')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgSpeaker') else ''
    audio_file_data.speaker_image_url = '{}{}'.format(SITE_URL, speaker_img_url_stub) if speaker_img_url_stub else ''

    album_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgItem')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgItem') else ''
    audio_file_data.album_image_url = '{}{}'.format(SITE_URL, album_img_url_stub) if album_img_url_stub else ''

    audio_file_data.details_url = details_url
    audio_file_data.download_url = download_url

    return audio_file_data


def download_file_from_page(session, audio_file_data):
    # generate name for this mp3 file
    filename = '{0}_{1}.mp3'.format(audio_file_data.id, audio_file_data.title.replace(' ', '_'))
    full_file_path = STORAGE_PATH + filename

    message = ''

    # assuming that worked
    file = session.get(audio_file_data.download_url, allow_redirects=True)
    if file.status_code == 200:
        with open(full_file_path, 'wb') as f:
            f.write(file.content)

        # get original file metadata
        # TODO: Check metatada from page against mp3 metadata & overwrite either where necessary. Prefer mp3 data
        # TODO: Save all original data as audiofile tag comment
        audiofile = eyed3.load(full_file_path)
        original_title = audiofile.tag.title
        original_album = audiofile.tag.album
        original_album_artist = audiofile.tag.album_artist
        original_artist = audiofile.tag.artist
        original_genre = audiofile.tag.genre
        original_track = audiofile.tag.track_num
        original_year = audiofile.tag.getBestDate()

        # cover image
        if audio_file_data.album_image_url != "":
            album_image = Image.open(urllib.request.urlopen(audio_file_data.album_image_url))
            album_image_bytes = io.BytesIO()
            album_image.save(album_image_bytes, format='PNG')
            album_image_bytes = album_image_bytes.getvalue()
            audiofile.tag.images.set(3, album_image_bytes, "image/jpeg", u"Description")

        # artist image
        if audio_file_data.speaker_image_url != "":
            artist_image = Image.open(urllib.request.urlopen(audio_file_data.speaker_image_url))
            artist_image_bytes = io.BytesIO()
            artist_image.save(artist_image_bytes, format='PNG')
            artist_image_bytes = artist_image_bytes.getvalue()
            audiofile.tag.images.set(8, artist_image_bytes, "image/jpeg", u"Description")

        # add appropriate metadata to audio file
        # TODO: full comparison of original metadata and metadata from page. Only use page if blank?
        # TODO: add ALL relevant data from audiofile.tag to audio_file_data
        if audiofile.tag.artist is None or audiofile.tag.artist == "":
            audiofile.tag.artist = audio_file_data.artist
        if audiofile.tag.album_artist is None or audiofile.tag.album_artist == "":
            audiofile.tag.album_artist = audio_file_data.album_artist
        audio_file_data.year = original_year

        # attach download and details links
        audiofile.tag.audio_file_url = audio_file_data.download_url
        audiofile.tag.audio_source_url = audio_file_data.details_url

        # definitely use page_data genre
        audiofile.tag.genre = audio_file_data.genre

        # finally save all metadata to mp3 file
        audiofile.tag.save()
        # confirm download on metadata class
        audio_file_data.download_successful = True

        message = "Download of {0} successful!".format(filename)
    else:
        message = "Download of {0} failed".format(filename)

    return message, audio_file_data


def attempt_file_download(session, file_id, metadata_only=False):
    # urls for details web page and download link
    details_url = '{site}/details.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)
    dl_url = '{site}/download.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)

    audio_file_data = get_file_data_from_page(session=session, details_url=details_url, download_url=dl_url)
    audio_file_data.id = file_id

    message = '{}{}'.format(audio_file_data.id, audio_file_data.title)

    # only download audio file if parameter says to
    if not metadata_only:
        message = download_file_from_page(session, audio_file_data)

    print(message)
    return {
        'message': message,
        'audio_file_data': audio_file_data
    }


def create_site_session():
    with requests.Session() as session:
        #  create session based on site login page
        login_url = '{site_url}/myaccount/login.aspx'.format(site_url=SITE_URL)
        login_page = session.get(login_url)

        # generate login data object based on site login form
        login_data = generate_login_data(login_page)

        # attempt login
        response = session.post(login_url, data=login_data)
        if response.status_code == 200:  # successful login
            return session
        else:
            return None


def download_single_audio_file(file_id, metadata_only=False):
    with create_site_session() as session:
        if session is not None:
            response = attempt_file_download(session, file_id, metadata_only=metadata_only)
            return response
        else:
            message = "Unable to log into site"
            print(message)
            return {
                'message': message
            }


def download_audio_file_range(initial_file_id, last_file_id, metadata_only=False):
    with create_site_session() as session:
        if session is not None:
            # assuming that worked:
            # start looping through every web page and see how it goes!
            files = []
            for file_id in range(int(initial_file_id), int(last_file_id) + 1):
                response = attempt_file_download(session, file_id, metadata_only=metadata_only)
                files.append(response)

            save_files_to_csv(files)

            return files

        else:
            files = []
            message = "Unable to log into site"
            print(message)
            message_json = {
                'message': message
            }
            files.append(message_json)
            return files

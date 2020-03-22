from bs4 import BeautifulSoup
import requests
import eyed3
import urllib.request
import io
from PIL import Image

import credentials
import settings

# use constants from settings page
STORAGE_PATH = settings.STORAGE_PATH
SITE_URL = settings.SITE_URL
LOGIN_URL = settings.LOGIN_URL

# use credentials from credentials page
USERNAME = credentials.USERNAME
PASSWORD = credentials.PASSWORD


def clean_string(html_element):
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


def attempt_file_download(session, file_id):
    # urls for details web page and download link
    details_url = '{site}/details.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)
    dl_url = '{site}/download.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)

    # down
    open_details_page = session.get(details_url)
    details_soup = BeautifulSoup(open_details_page.content, 'lxml')

    # get metadata from page
    content = details_soup.find('td', class_='content')

    # Title = Title
    title = clean_string(content.h1) if content.h1 else ''
    # Album = Organization
    album = clean_string(content.find(id='ctl00_ContentPlaceHolder_hypOrganization'))
    # Album Artist = Group/Ministry
    album_artist = clean_string(content.find(id='ctl00_ContentPlaceHolder_panelProductGroups'))
    # Artist = Speaker
    speaker = clean_string(content.find(id='ctl00_ContentPlaceHolder_hypSpeaker'))
    # Genre = Topic
    genre = clean_string(content.find(id='ctl00_ContentPlaceHolder_hypTopic'))
    # Comment = Description + Speaker
    # comment = content.find(id='').text
    # Description
    description = content.p.text if content.p else ''
    # Track  # = Series (have to parse because it's formatted as Part x of a y part series. You can see how I did it in the spreadsheet)
    raw_track_info = clean_string(content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'))
    track_data = [x for x in raw_track_info.split() if x.isdigit()] if raw_track_info else ''
    track_number = track_data[0] if len(track_data) == 2 else 0
    total_tracks = track_data[1] if len(track_data) == 2 else 0
    # Year / Date = Date
    # year = dl_soup.find(id='').text

    # image urls
    speaker_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgSpeaker')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgSpeaker') else ''
    speaker_img_url = '{}{}'.format(SITE_URL, speaker_img_url_stub) if speaker_img_url_stub else ''

    album_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgItem')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgItem') else ''
    album_img_url = '{}{}'.format(SITE_URL, album_img_url_stub) if album_img_url_stub else ''

    # generate name for this mp3 file
    filename = '{0}_{1}.mp3'.format(file_id, title.replace(' ', '_'))
    fullpath = STORAGE_PATH + filename

    # assuming that worked
    file = session.get(dl_url, allow_redirects=True)
    if file.status_code == 200:
        with open(fullpath, 'wb') as f:
            f.write(file.content)

        # get original file metadata
        audiofile = eyed3.load(fullpath)
        original_title = audiofile.tag.title
        original_album = audiofile.tag.album
        original_album_artist = audiofile.tag.album_artist
        original_artist = audiofile.tag.artist
        original_genre = audiofile.tag.genre
        original_track = audiofile.tag.track_num
        original_year = audiofile.tag.getBestDate()

        # cover image
        if album_img_url == "":
            album_image = Image.open(urllib.request.urlopen(album_img_url))
            album_image_bytes = io.BytesIO()
            album_image.save(album_image_bytes, format='PNG')
            album_image_bytes = album_image_bytes.getvalue()
            audiofile.tag.images.set(3, album_image_bytes, "image/jpeg", u"Description")

        # artist image
        if speaker_img_url == "":
            artist_image = Image.open(urllib.request.urlopen(speaker_img_url))
            artist_image_bytes = io.BytesIO()
            artist_image.save(artist_image_bytes, format='PNG')
            artist_image_bytes = artist_image_bytes.getvalue()
            audiofile.tag.images.set(8, artist_image_bytes, "image/jpeg", u"Description")

        # add appropriate metadata to audio file
        if audiofile.tag.artist == "":
            audiofile.tag.artist = speaker
        if audiofile.tag.album_artist == "":
            audiofile.tag.album_artist = album_artist
        audiofile.tag.audio_file_url = dl_url
        audiofile.tag.audio_source_url = details_url
        audiofile.tag.genre = genre
        audiofile.tag.save()

        print("Download of {0} successful!".format(filename))
    else:
        print("Download of {0} failed".format(filename))


def create_site_session():
    with requests.Session() as session:
        #  create session based on site login page
        login_page = session.get(LOGIN_URL)

        # generate login data object based on site login form
        login_data = generate_login_data(login_page)

        # attempt login
        response = session.post(LOGIN_URL, data=login_data)
        if response.status_code == 200:  # successful login
            return session
        else:
            return None


def download_single_file(file_id):
    with create_site_session() as session:
        if session is not None:
            attempt_file_download(session, file_id)
        else:
            print("Unable to log into site")


def download_file_range(initial_file_id, last_file_id):
    with create_site_session() as session:
        if session is not None:
            # assuming that worked:
            # start looping through every web page and see how it goes!
            for file_id in range(initial_file_id, last_file_id + 1):
                attempt_file_download(session, file_id)
        else:
            print("Unable to log into site")


download_single_file(2)

from bs4 import BeautifulSoup
import requests
import eyed3
import pandas as pd
import time
import datetime
import dataclasses

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
    return remove_extra_whitespace(html_element.text)


def remove_extra_whitespace(input: str) -> str:
    return " ".join(input.split())


def clean_dataclass_string_fields(instance):
    if not dataclasses.is_dataclass(instance):
        return instance
    for field in instance.__dataclass_fields__:
        current_val = getattr(instance, field)
        if isinstance(current_val, str):
            clean_val = remove_extra_whitespace(current_val)
            setattr(instance, field, clean_val)
    return instance


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


def get_file_data_from_page(session, details_url, download_url):
    open_details_page = session.get(details_url)
    details_soup = BeautifulSoup(open_details_page.content, 'lxml')

    # get metadata from page
    content = details_soup.find('div', class_='content')

    audio_file_data = AudioFileData()

    # Title = Title
    audio_file_data.title = details_soup.find("meta", property="og:title")["content"]
    audio_file_data.title = audio_file_data.title.replace(" - WordMp3.com", "")

    # Album Artist = Organization
    organization = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypOrganization'))
    audio_file_data.album_artist = organization if organization else ''

    # Genre = Type / Topic
    type = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelItemType')).replace("Type:", "")
    topic = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypTopic'))
    if type and topic:
        audio_file_data.genre = '{}: {}'.format(type, topic)
    elif type:
        audio_file_data.genre = type
    elif topic:
        audio_file_data.genre = topic
    else:
        audio_file_data.genre = ''

    # Artist = Speaker
    speaker = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypSpeaker'))
    audio_file_data.artist = speaker if speaker else ''

    #Album
    # if it's part of a series
    if content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'):
        # and has one or more related groups,
        groups_section = content.find(id='ctl00_ContentPlaceHolder_panelProductGroups')
        if groups_section:
            # use the first related group
            table = groups_section.find("table")
            rows = table.find_all("tr")
            for row in rows:
                columns = row.find_all("td")
                for column in columns:
                    links = column.find_all("a")
                    for link in links:
                        audio_file_data.album = link.text
                        if len(audio_file_data.album) > 0:
                            break
                    if len(audio_file_data.album) > 0:
                        break
                if len(audio_file_data.album) > 0:
                    break
        # no related groups,
        elif not groups_section:
            # use Organization: Topic
            if organization:
                audio_file_data.album = "{}: {}".format(organization, topic)
            else:
                # If it's part of a series and has no related groups and no organization, Speaker: Topic
                audio_file_data.album = "{}: {}".format(speaker, topic)
    # If it's NOT part of a series, use WordMP3: Organization
    else:
        if organization:
            audio_file_data.album = "WordMP3: {}".format(organization)
        else:
            audio_file_data.album = "WordMP3: {}".format(topic)

    # Comment = Description + Speaker
    # page_data['comment'] = content.find(id='').text
    # Description
    for tag in details_soup.find_all("meta"):
        if tag.get("name", None) == "description":
            audio_file_data.description = tag["content"]
            break

    # year
    date = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelDate'))
    if date:
        date = date.replace("Date:", "").strip()
        try:
            audio_file_data.year = datetime.datetime.strptime(date, '%m/%d/%Y').year
        except:
            audio_file_data.year = date
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

    # clean all string fields
    audio_file_data = clean_dataclass_string_fields(audio_file_data)

    return audio_file_data


def download_file_from_page(session, audio_file_data):

    audio_file_data.last_download_attempt = datetime.datetime.now()

    # generate name for this mp3 file
    file_id = str(audio_file_data.id).rjust(7, '0')
    file_title = audio_file_data.title.replace(' ', '_')
    filename = '{0}_{1}.mp3'.format(file_id, file_title)
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

        original_comments = audiofile.tag.comments

        # cover image
        if audio_file_data.album_image_url != "":
            try:
                album_img_resp = requests.get(audio_file_data.album_image_url)
                album_img_bytes = album_img_resp.content
                audiofile.tag.images.set(3, album_img_bytes, "image/jpeg", u"Description")
            except Exception as e:
                print(f"Error downloading album cover image from { audio_file_data.album_image_url }: \n{ e }")

        # artist image
        if audio_file_data.speaker_image_url != "":
            try:
                speaker_img_resp = requests.get(audio_file_data.speaker_image_url)
                speaker_img_bytes = speaker_img_resp.content
                audiofile.tag.images.set(8, speaker_img_bytes, "image/jpeg", u"Description")
            except Exception as e:
                print(f"Error downloading speaker image from { audio_file_data.speaker_image_url }: \n{ e }")

        # add appropriate metadata to audio file
        # TODO: full comparison of original metadata and metadata from page. Only use page if blank?
        # TODO: add ALL relevant data from audiofile.tag to audio_file_data
        audiofile.tag.album = audio_file_data.album

        if audio_file_data.artist:
            audiofile.tag.artist = audio_file_data.artist

        if audio_file_data.album_artist:
            audio_file_data.album_artist = audio_file_data.album_artist

        if original_year:
            audiofile.tag.year = original_year
        elif audio_file_data.year:
            audiofile.tag.year = audio_file_data.year

        # attach download and details links
        audiofile.tag.audio_file_url = audio_file_data.download_url
        audiofile.tag.audio_source_url = audio_file_data.details_url

        # definitely use page_data genre
        audiofile.tag.genre = audio_file_data.genre

        try:

            comments = u"Original metadata:\n"
            comments += u"Title: {}\n".format(original_title)
            comments += u"Album: {}\n".format(original_album)
            comments += u"Artist: {}\n".format(original_artist)
            comments += u"Album Artist: {}\n".format(original_album_artist)
            comments += u"Genre: {}\n".format(original_genre)
            comments += u"Track: {}\n".format(original_track)
            comments += u"Year: {}\n".format(original_year)
            comments += u"Original Comments:\n"

            for comment in original_comments:
                comments += comment.text

            audiofile.tag.comments.set(comments)
        except:
            message = "couldn't set comments"

        try:
            # finally save all metadata to mp3 file
            audiofile.tag.save()
            # confirm download on metadata class
            audio_file_data.download_successful = True
        except:
            message = "Download of {0} failed".format(filename)

        message = "Download of {0} successful!".format(filename)
    else:
        message = "Download of {0} failed".format(filename)

    return message, audio_file_data


def attempt_file_download(session, file_id, metadata_only=False, redownload=False):
    # urls for details web page and download link
    details_url = '{site}/details.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)
    dl_url = '{site}/download.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)

    audio_file_data = get_file_data_from_page(session=session, details_url=details_url, download_url=dl_url)
    audio_file_data.id = file_id

    message = '{} - {}'.format(audio_file_data.id, audio_file_data.title)

    # only download audio file if parameter says to
    if not metadata_only: # or redownload:
        message, audio_file_data = download_file_from_page(session, audio_file_data)

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
            metadata = csv_to_audiofiledata_list(CSV_OUTPUT_FILE)
            metadata_ids = [x.id for x in metadata]
            response = attempt_file_download(session, file_id, metadata_only=metadata_only)
            file = response['audio_file_data']
            if file.id in metadata_ids:
                metadata = [file if file.id == x.id else x for x in metadata]
            else:
                metadata.append(file)
            save_list_of_files_to_csv(metadata, CSV_OUTPUT_FILE)
            return response
        else:
            message = "Unable to log into site"
            print(message)
            return {
                'message': message
            }


def download_audio_file_range(initial_file_id, last_file_id, metadata_only=False, redownload=False):
    with create_site_session() as session:
        if session is not None:
            # assuming that worked:
            # start looping through every web page and see how it goes!
            metadata = csv_to_audiofiledata_list(CSV_OUTPUT_FILE)
            metadata_ids = [x.id for x in metadata]
            files = []
            for file_id in range(int(initial_file_id), int(last_file_id) + 1):
                current_file = next(iter([x for x in metadata if x.id == file_id]), None)
                if redownload or (current_file is None) or (current_file is not None and not current_file.download_successful):
                    try:
                        response = attempt_file_download(session, file_id, metadata_only=metadata_only,
                                                         redownload=redownload)
                        files.append(response)
                        # not the most efficient, but I really want to make sure that data isn't lost if this loop breaks
                        file = response['audio_file_data']
                        if file.id in metadata_ids:
                            metadata = [file if file.id == x.id else x for x in metadata]
                        else:
                            metadata.append(file)
                    except:
                        # TODO: Log these errors somewhere
                        pass
                # attempt to save csv every loop to always have updated data.
                save_list_of_files_to_csv(metadata, CSV_OUTPUT_FILE)
                # wait one second so as not to overload their poor servers
                time.sleep(1)

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


def download_all_files(metadata_only=False):
    # check for metadata.
    metadata = csv_to_audiofiledata_list(CSV_OUTPUT_FILE)
    # if no metadata, create it?

    # then download all files?
    pass


def csv_to_audiofiledata_list(csv_filepath):

    files = []

    try:
        # create dataframe from csv
        dataframe = pd.read_csv(csv_filepath)

        # dataframe to audiofiles
        files = [(AudioFileData(id=row.id,
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
                                last_download_attempt=row.last_download_attempt)) for i, row in dataframe.iterrows()]
    except:
        # TODO: Log something
        pass

    return files


def save_list_of_files_to_csv(files, output_file_path):
    if len(files) > 0:
        try:
            # get files from input
            # files = [x['audio_file_data'] for x in files]
            # sort files
            files = sorted(files, key=lambda e: int(e.id))
            # get class attributes
            fields = vars(files[0]).keys()
            # create dataframe from list of audiofiles and fields
            dataframe = pd.DataFrame([[getattr(i, j) for j in fields] for i in files], columns=fields)
            # save dataframe to csv
            dataframe.to_csv(output_file_path, index=False)
        except:
            # TODO: log these errors somewhere
            pass

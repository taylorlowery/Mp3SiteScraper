import os.path

from bs4 import BeautifulSoup
import requests
import eyed3
import pandas as pd
import time
import datetime
import dataclasses
from dictor import dictor
from dataclasses import fields
import credentials
import settings

from MetadataRow import MetadataRow, FileData, MiscellaneousMetadata, SiteMetadata
from typing import List

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
    for field in [f.name for f in fields(instance)]:
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

    audio_file_data = MetadataRow()

    # Title = Title
    audio_file_data.site_Title = details_soup.find("meta", property="og:title")["content"]
    audio_file_data.site_Title = audio_file_data.site_Title.replace(" - WordMp3.com", "")

    # Album Artist = Organization
    organization = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypOrganization'))
    audio_file_data.site_Organization = organization if organization else ''

    ministry = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypMinistry'))
    audio_file_data.site_Ministry = ministry if ministry else ''

    groups = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelProductGroups'))
    audio_file_data.site_Groups = groups if groups else ''

    price = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_lblPrice'))
    audio_file_data.site_Price = price if price else ''

    # Genre = Type / Topic
    type = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelItemType')).replace("Type:", "")
    topic = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypTopic'))
    audio_file_data.site_Type = type if type else ''
    audio_file_data.site_Topic = topic if topic else ''

    if type and topic:
        audio_file_data.file_Genre = '{}: {}'.format(type, topic)
    elif type:
        audio_file_data.file_Genre = type
    elif topic:
        audio_file_data.file_Genre = topic
    else:
        audio_file_data.file_Genre = ''

    # Artist = Speaker
    speaker = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypSpeaker'))
    audio_file_data.site_Speaker = speaker if speaker else ''

    #Album
    # if it's part of a series
    series_number = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'))
    audio_file_data.site_SeriesNumber = series_number if series_number else ''
    if series_number:

        # format parts number
        parts = series_number.split()
        audio_file_data.site_series_number_formatted = f"{parts[1]}/{parts[4]}"

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
                        audio_file_data.file_Album = link.text
                        if len(audio_file_data.file_Album) > 0:
                            break
                    if len(audio_file_data.file_Album) > 0:
                        break
                if len(audio_file_data.file_Album) > 0:
                    break
        # no related groups,
        elif not groups_section:
            # use Organization: Topic
            if organization:
                audio_file_data.file_Album = "{}: {}".format(organization, topic)
            else:
                # If it's part of a series and has no related groups and no organization, Speaker: Topic
                audio_file_data.file_Album = "{}: {}".format(speaker, topic)
    # If it's NOT part of a series, use WordMP3: Organization
    else:
        if organization:
            audio_file_data.file_Album = "WordMP3: {}".format(organization)
        else:
            audio_file_data.file_Album = "WordMP3: {}".format(topic)

    # Comment = Description + Speaker
    # page_data['comment'] = content.find(id='').text
    # Description
    for tag in details_soup.find_all("meta"):
        if tag.get("name", None) == "description":
            audio_file_data.site_Description = tag["content"]
            break

    # year
    date = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelDate'))
    if date:
        date = date.replace("Date:", "").strip()
        try:
            audio_file_data.site_Date = datetime.datetime.strptime(date, '%m/%d/%Y').year
        except:
            audio_file_data.site_Date = date
    else:
        audio_file_data.site_Date = ''
    # Track  # = Series (have to parse because it's formatted as Part x of a y part series.
    # You can see how I did it in the spreadsheet)
    raw_track_info = clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'))
    track_data = [x for x in raw_track_info.split() if x.isdigit()] if raw_track_info else ''
    audio_file_data.site_SeriesNumber = track_data[0] if len(track_data) == 2 else None

    # audio_file_data.total_tracks = track_data[1] if len(track_data) == 2 else None
    # Year / Date = Unfortunately, no consistent date found on web page. Have to get it from the file

    # image urls
    speaker_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgSpeaker')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgSpeaker') else ''
    audio_file_data.site_speaker_image_url = '{}{}'.format(SITE_URL, speaker_img_url_stub) if speaker_img_url_stub else ''

    album_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgItem')['src'] if content.find(
        id='ctl00_ContentPlaceHolder_imgItem') else ''
    audio_file_data.album_image_url = '{}{}'.format(SITE_URL, album_img_url_stub) if album_img_url_stub else ''

    audio_file_data.details_url = details_url
    audio_file_data.site_download_url = download_url

    if content.find(id='ctl00_ContentPlaceHolder_hypPDFOutline2'):
        audio_file_data.has_outline = True

    # clean all string fields
    audio_file_data = clean_dataclass_string_fields(audio_file_data)

    return audio_file_data


def download_file_from_page(session, audio_file_data: MetadataRow):

    audio_file_data.file_download_last_attempt = datetime.datetime.now()

    # get initial filetype
    r = session.head(audio_file_data.site_download_url, allow_redirects=True)
    original_file_name = dictor(r.headers, "Content-Disposition").replace("attachment; filename=", "")
    file_size_str = dictor(r.headers, "Content-Length")
    if file_size_str:
        audio_file_data.file_size = int(file_size_str)
    audio_file_data.file_filename_original = original_file_name
    audio_file_data.file_ext = original_file_name.split(".")[-1] if original_file_name else ".mp3"

    # generate name for this mp3 file
    file_id = str(audio_file_data.site_ID).rjust(7, '0')
    file_title = original_file_name.replace(' ', '_')
    audio_file_data.file_filename_current = '{0}_{1}'.format(file_id, file_title)
    full_file_path = f"{STORAGE_PATH}{audio_file_data.file_filename_current}.{audio_file_data.file_ext}"

    message = ''

    # assuming that worked
    file = session.get(audio_file_data.site_download_url, allow_redirects=True)

    if file.status_code == 200:
        with open(full_file_path, 'wb') as f:
            f.write(file.content)

        # get original file metadata
        audiofile = eyed3.load(full_file_path)
        audio_file_data.file_Title_Original = audiofile.tag.title
        audio_file_data.file_Album = audiofile.tag.album
        audio_file_data.file_Album_Artist = audiofile.tag.album_artist
        audio_file_data.file_Artist_Original = audiofile.tag.artist
        audio_file_data.file_Publisher = audiofile.tag.publisher
        audio_file_data.file_Genre = audiofile.tag.genre
        track, total_tracks = dictor(audiofile.tag.track_num)
        audio_file_data.file_Track = track
        audio_file_data.total_tracks = total_tracks
        audio_file_data.file_Year = audiofile.tag.getBestDate()

        original_comments = audiofile.tag.comments

        # cover image
        if audio_file_data.album_image_url != "":
            try:
                album_img_resp = requests.get(audio_file_data.album_image_url)
                album_img_bytes = album_img_resp.content
                audiofile.tag.images.set(3, album_img_bytes, "image/jpeg")
            except Exception as e:
                print(f"Error downloading album cover image from { audio_file_data.album_image_url }: \n{ e }")

        # artist image
        if audio_file_data.site_speaker_image_url != "":
            try:
                speaker_img_resp = requests.get(audio_file_data.site_speaker_image_url)
                speaker_img_bytes = speaker_img_resp.content
                audiofile.tag.images.set(8, speaker_img_bytes, "image/jpeg")
            except Exception as e:
                print(f"Error downloading speaker image from { audio_file_data.site_speaker_image_url }: \n{ e }")

        # add appropriate metadata to audio file
        # TODO: full comparison of original metadata and metadata from page. Only use page if blank?
        # TODO: add ALL relevant data from audiofile.tag to audio_file_data

        # use original mp3 title if present
        if audio_file_data.file_Title_Original and len(audio_file_data.file_Title_Original) > 0:
            audiofile.tag.title = audio_file_data.file_Title_Original
            audio_file_data.site_Title = audio_file_data.file_Title_Original
        else:
            audiofile.tag.site_Title = audio_file_data.site_Title

        if not audio_file_data.file_Album or len(audio_file_data.file_Album) == 0:
            audiofile.tag.album = audio_file_data.file_Album

        if audio_file_data.file_Artist:
            audiofile.tag.artist = audio_file_data.file_Artist

        if audio_file_data.file_Album_Artist:
            audiofile.tag.album_artist = audio_file_data.file_Album_Artist

        if audio_file_data.file_Year:
            audiofile.tag.release_date = audio_file_data.file_Year

        # attach download and details links
        audiofile.tag.audio_file_url = audio_file_data.site_download_url
        audiofile.tag.audio_source_url = audio_file_data.details_url

        # definitely use page_data genre
        audiofile.tag.genre = audio_file_data.file_Genre

        try:

            comments = u"Original metadata:\n"
            comments += u"Title: {}\n".format(audio_file_data.file_Title_Original)
            comments += u"Album: {}\n".format(audio_file_data.file_Album)
            comments += u"Artist: {}\n".format(audio_file_data.file_Artist)
            comments += u"Album Artist: {}\n".format(audio_file_data.file_Album_Artist)
            comments += u"Genre: {}\n".format(audio_file_data.file_Genre)
            comments += u"Track: {}\n".format(audio_file_data.file_Track)
            comments += u"Year: {}\n".format(audio_file_data.file_Year)
            comments += u"Original Comments:\n"

            for comment in original_comments:
                comments += comment.text

            audiofile.tag.comments.set(comments)
            audio_file_data.file_Comment = "\n".join([c.text for c in original_comments])

        except Exception as ex:
            message = f"Couldn't set mp3 comments: { ex }"

        try:
            # finally save all metadata to mp3 file
            audiofile.tag.save()
            # confirm download on metadata class
            audio_file_data.file_download_success = True
            audio_file_data.file_download_path = full_file_path
        except Exception as ex:
            message = "Download of {0} failed: {1}".format(audio_file_data.file_filename_current, ex)

        # create directory structure for album
        try:
            # f"{STORAGE_PATH}{filename}.{file_extension}"
            filename = f"{ file_id }_{ audio_file_data.site_Title }.{ audio_file_data.file_ext }"
            album_file_path = os.path.join(STORAGE_PATH, audio_file_data.file_Album.replace(":", ""))
            if not os.path.isdir(album_file_path):
                os.mkdir(album_file_path)
            file_path_with_album_dir = os.path.join(album_file_path, audio_file_data.file_filename_current)
            os.replace(full_file_path, file_path_with_album_dir)
            audio_file_data.file_download_path = file_path_with_album_dir
        except Exception as ex:
            print(f"Unable to move { full_file_path } to album directory after download: { ex }")

        message = "Download of {0} successful!".format(audio_file_data.file_filename_current)
    else:
        message = "Download of {0} failed".format(audio_file_data.file_filename_current)

    # download outline
    if audio_file_data.has_outline:
        try:
            outline_dl_url = f"{SITE_URL}/files/outlines/{audio_file_data.site_ID}.pdf"
            outline_resp = requests.get(outline_dl_url)
            if outline_resp.ok:
                outline_filename = f"{ STORAGE_PATH }{ audio_file_data.file_filename_current }_outline.pdf"
                with open(outline_filename, "wb") as f:
                    f.write(outline_resp.content)
        except Exception as e:
            print(f"Error downloading outline for file { audio_file_data.site_ID }: { e }")

    return message, audio_file_data


def attempt_file_download(session, file_id, metadata_only=False, redownload: bool = False):
    # urls for details web page and download link
    details_url = '{site}/details.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)
    dl_url = '{site}/download.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)

    audio_file_data = get_file_data_from_page(session=session, details_url=details_url, download_url=dl_url)
    audio_file_data.site_ID = file_id

    message = '{} - {}'.format(audio_file_data.site_ID, audio_file_data.site_Title)

    # only download audio file if parameter says to
    if not metadata_only or redownload:
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


def download_single_audio_file(file_id, metadata_only=False, redownload: bool = False):
    with create_site_session() as session:
        if session is not None:
            metadata = csv_to_audiofiledata_list(CSV_OUTPUT_FILE)
            metadata_ids = [x.site_ID for x in metadata]
            response = attempt_file_download(session, file_id, metadata_only=metadata_only, redownload=redownload)
            file = response['audio_file_data']
            if int(file.site_ID) in metadata_ids:
                metadata = [file if int(file.site_ID) == x.site_ID else x for x in metadata]
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
            metadata_ids = [x.site_ID for x in metadata]
            files = []
            for file_id in range(int(initial_file_id), int(last_file_id) + 1):
                current_file = next(iter([x for x in metadata if x.site_ID == file_id]), None)
                # download file if it is supposed to be redownloaded, or if it has not been downloaded ever, or previous file download was unsuccessful
                if redownload or (current_file is None) or (current_file is not None and not current_file.file_download_success):
                    try:
                        response = attempt_file_download(session, file_id, metadata_only=metadata_only, redownload=redownload)
                        files.append(response)
                        # not the most efficient, but I really want to make sure that data isn't lost if this loop breaks
                        file = response['audio_file_data']
                        if file.site_ID in metadata_ids:
                            metadata = [file if file.site_ID == x.site_ID else x for x in metadata]
                        else:
                            metadata.append(file)
                    except Exception as ex:
                        print(f"Error downloading file { file_id }: { ex }")
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
        files = []
        for i, row in dataframe.iterrows():
            a = MetadataRow()
            for field in [f.name for f in fields(MetadataRow)]:
                setattr(a, field, getattr(row, field))
            files.append(a)

    except Exception as ex:
        print(f"Error reading metadata csv at { csv_filepath }: { ex }")

    return files


def save_list_of_files_to_csv(files: List[MetadataRow], output_file_path):
    if len(files) > 0:
        try:
            # get files from input
            # files = [x['audio_file_data'] for x in files]
            # sort files
            files = sorted(files, key=lambda e: int(e.site_ID))
            # get class attributes
            metadata_fields = []
            metadata_fields.extend([f.name for f in fields(SiteMetadata)])
            metadata_fields.extend([f.name for f in fields(FileData)])
            metadata_fields.extend([f.name for f in fields(MiscellaneousMetadata)])

            # create dataframe from list of audiofiles and fields
            dataframe = pd.DataFrame([[getattr(i, j) for j in metadata_fields] for i in files], columns=metadata_fields)
            # save dataframe to csv
            dataframe.to_csv(output_file_path, index=False)
        except Exception as ex:
            print(f"Error saving metadata file at { output_file_path }: { ex }")

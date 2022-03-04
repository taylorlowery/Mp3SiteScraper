import datetime
import os.path
import time
from dataclasses import fields
from typing import List

import eyed3
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dictor import dictor

from MetadataRow import MetadataRow, FileData, MiscellaneousMetadata, SiteMetadata
from credentials import USERNAME, PASSWORD
from settings import CSV_OUTPUT_PATH, SITE_URL, STORAGE_PATH, SECONDS_BETWEEN_DOWNLOADS
from utils import Utilities

BROWSER_REQUEST_HEADERS = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "DNT": "1",
            "Host": "www.wordmp3.com",
            "Referer": "https://www.wordmp3.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Sec-GPC": "1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        }

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


def scrape_single_page(session, file_id: int) -> MetadataRow:
    audio_file_data = MetadataRow(site_ID=file_id)
    details_url = '{site}/details.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)
    download_url = '{site}/download.aspx?id={file_id}'.format(site=SITE_URL, file_id=file_id)

    r = session.head(details_url, headers=BROWSER_REQUEST_HEADERS, allow_redirects=True)

    open_details_page = session.get(details_url, headers=BROWSER_REQUEST_HEADERS)
    details_soup = BeautifulSoup(open_details_page.content, 'lxml')

    warning_html = details_soup.find(id="ctl00_ContentPlaceHolder_Notification1_panelNotification")
    warning = Utilities.clean_html_contents(warning_html)
    # TODO: further handling of pages without content
    if warning == "The item you requested could not be found.":
        audio_file_data.notes = warning
        return audio_file_data

    # get metadata from page
    content = details_soup.find('div', class_='content')

    if content:


        # Title = Title
        audio_file_data.site_Title = details_soup.find("meta", property="og:title")["content"]
        audio_file_data.site_Title = audio_file_data.site_Title.replace(" - WordMp3.com", "")
        audio_file_data.site_title_formatted = Utilities.format_site_title(audio_file_data.site_Title)

        # Album Artist = Organization
        organization = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypOrganization'))
        audio_file_data.site_Organization = organization if organization else ""

        ministry = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypMinistry'))
        audio_file_data.site_Ministry = ministry if ministry else ""

        group_section = content.find(id='ctl00_ContentPlaceHolder_panelProductGroups')
        groups = None
        if group_section:
            group_link = group_section.find('a')
            if group_link:
                groups = group_link.get('title')
        audio_file_data.site_Groups = groups if groups else ""

        price = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_lblPrice'))
        audio_file_data.site_Price = price if price else ""

        # Genre = Type / Topic
        type = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelItemType')).replace("Type:", "")
        topic = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_hypTopic'))
        audio_file_data.site_Type = type if type else ""
        audio_file_data.site_Topic = topic if topic else ""

        # Artist = Speaker
        speaker_html = content.find(id='ctl00_ContentPlaceHolder_hypSpeaker')
        speaker = Utilities.clean_html_contents(speaker_html)
        audio_file_data.site_Speaker = speaker if speaker else ""
        if speaker:
            audio_file_data.site_speaker_formatted = Utilities.format_site_speaker_name(audio_file_data.site_Speaker)
        speaker_url = speaker_html["href"]
        if speaker_url:
            audio_file_data.site_speaker_url = f"{ SITE_URL }{speaker_url}"
            speaker_id_str = speaker_url.replace("/speakers/profile.aspx?id=", "")
            if speaker_id_str:
                speaker_id = int(speaker_id_str)
                audio_file_data.site_speaker_id = speaker_id


        # Comment = Description + Speaker
        # page_data['comment'] = content.find(id=").text
        # Description
        for tag in details_soup.find_all("meta"):
            if tag.get("name", None) == "description":
                audio_file_data.site_Description = tag["content"]
                break

        # year
        date = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelDate'))
        if date:
            date = date.replace("Date:", "").strip()
            try:
                audio_file_data.site_Date = datetime.datetime.strptime(date, '%m/%d/%Y').year
            except:
                audio_file_data.site_Date = date
        else:
            audio_file_data.site_Date = ""
        # Track  # = Series (have to parse because it's formatted as Part x of a y part series.
        # You can see how I did it in the spreadsheet)
        raw_track_info = Utilities.clean_html_contents(content.find(id='ctl00_ContentPlaceHolder_panelSeriesNumber'))
        track_data = [x for x in raw_track_info.split() if x.isdigit()] if raw_track_info else ""
        audio_file_data.site_SeriesNumber = track_data[0] if len(track_data) == 2 else None

        # audio_file_data.total_tracks = track_data[1] if len(track_data) == 2 else None
        # Year / Date = Unfortunately, no consistent date found on web page. Have to get it from the file

        # image urls
        speaker_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgSpeaker')['src'] if content.find(
            id='ctl00_ContentPlaceHolder_imgSpeaker') else ""
        audio_file_data.site_speaker_image_url = '{}{}'.format(SITE_URL, speaker_img_url_stub) if speaker_img_url_stub else ""

        album_img_url_stub = content.find(id='ctl00_ContentPlaceHolder_imgItem')['src'] if content.find(
            id='ctl00_ContentPlaceHolder_imgItem') else ""
        audio_file_data.album_image_url = '{}{}'.format(SITE_URL, album_img_url_stub) if album_img_url_stub else ""

        audio_file_data.site_details_url = details_url
        audio_file_data.site_download_url = download_url

        if content.find(id='ctl00_ContentPlaceHolder_hypPDFOutline2'):
            audio_file_data.has_outline = True
            audio_file_data.site_outline_url = f"{SITE_URL}/files/outlines/{audio_file_data.site_ID}.pdf"

        # clean all string fields
        audio_file_data = Utilities.clean_dataclass_string_fields(audio_file_data)

        return audio_file_data


def download_file_from_page(session, audio_file_data: MetadataRow):

    audio_file_data.file_download_last_attempt = datetime.datetime.now()

    # get initial filetype
    r = session.head(audio_file_data.site_download_url, headers=BROWSER_REQUEST_HEADERS, allow_redirects=True)
    original_file_name = dictor(r.headers, "Content-Disposition").replace("attachment; filename=", "")
    file_size_str = dictor(r.headers, "Content-Length")
    if file_size_str:
        audio_file_data.file_size = int(file_size_str)
    audio_file_data.file_filename_original = original_file_name
    audio_file_data.file_ext = original_file_name.split(".")[-1] if original_file_name else ".mp3"

    # generate name for this mp3 file
    file_id = str(audio_file_data.site_ID).rjust(7, '0')
    file_title = original_file_name.replace(' ', '_')
    audio_file_data.file_Title = file_title
    audio_file_data.file_filename_current = '{0}_{1}'.format(file_id, file_title)
    full_file_path = f"{STORAGE_PATH}{audio_file_data.file_filename_current}"
    if not full_file_path.endswith(audio_file_data.file_ext):
        full_file_path = f"{full_file_path}.{audio_file_data.file_ext}"

    message = ""

    # assuming that worked
    file = session.get(audio_file_data.site_download_url, headers=BROWSER_REQUEST_HEADERS, allow_redirects=True)

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

        audiofile.tag.clear()

        # cover image
        if audio_file_data.album_image_url != "":
            try:
                album_img_resp = session.get(audio_file_data.album_image_url, headers=BROWSER_REQUEST_HEADERS)
                album_img_bytes = album_img_resp.content
                audiofile.tag.images.set(3, album_img_bytes, "image/jpeg")
            except Exception as e:
                print(f"Error downloading album cover image from { audio_file_data.album_image_url }: \n{ e }")

        # artist image
        if audio_file_data.site_speaker_image_url != "":
            try:
                speaker_img_resp = session.get(audio_file_data.site_speaker_image_url)
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
        audiofile.tag.audio_source_url = audio_file_data.site_details_url

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

        except Exception as ex:
            audio_file_data.file_download_success = False
            message = "Download of {0} failed: {1}\n".format(audio_file_data.file_filename_current, ex)

        if audio_file_data.file_download_success:
            # create directory structure for album
            try:
                # f"{STORAGE_PATH}{filename}.{file_extension}"
                album_file_path = STORAGE_PATH
                if audio_file_data.file_Album and len(audio_file_data.file_Album) > 0:
                    album_file_path = os.path.join(STORAGE_PATH, audio_file_data.file_Album.replace(":", ""))
                album_file_path = album_file_path.strip()

                if not os.path.isdir(album_file_path):
                    os.mkdir(album_file_path)

                file_path_with_album_dir = os.path.join(album_file_path, audio_file_data.file_filename_current)

                if os.path.isfile(full_file_path):
                    os.replace(full_file_path, file_path_with_album_dir)
                audio_file_data.file_download_path = album_file_path

                message = "Download of {0} successful!\n".format(audio_file_data.file_filename_current)
            except Exception as ex:
                print(f"Unable to move { full_file_path } to album directory after download: { ex }\n")

    else:
        message = "Download of {0} failed".format(audio_file_data.file_filename_current)

    # download outline
    if audio_file_data.has_outline:
        try:
            outline_resp = session.get(audio_file_data.site_outline_url)
            if outline_resp.ok:
                outline_filename = f"{ STORAGE_PATH }{ audio_file_data.file_filename_current }_outline.pdf"
                with open(outline_filename, "wb") as f:
                    f.write(outline_resp.content)
        except Exception as e:
            print(f"Error downloading outline for file { audio_file_data.site_ID }: { e }")

    return message, audio_file_data


def attempt_file_download(session, file_id, metadata_only=False, redownload: bool = False):
    # urls for details web page and download link

    audio_file_data = scrape_single_page(session=session, file_id=file_id)

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

        login_page_resp = session.get(login_url, headers=BROWSER_REQUEST_HEADERS)
        if not login_page_resp.ok:
            print(login_page_resp.text)
            return None
        # generate login data object based on site login form
        login_data = generate_login_data(login_page_resp)

        # attempt login
        response = session.post(login_url, headers=BROWSER_REQUEST_HEADERS, data=login_data)
        if response.status_code == 200:  # successful login
            return session
        else:
            print(response.text)
            return None


def download_single_audio_file(file_id, metadata_only=False, redownload: bool = False):
    with create_site_session() as session:
        if session is not None:
            metadata = csv_to_audiofiledata_list(CSV_OUTPUT_PATH)
            metadata_ids = [x.site_ID for x in metadata]
            response = attempt_file_download(session, file_id, metadata_only=metadata_only, redownload=redownload)
            file = response['audio_file_data']
            if int(file.site_ID) in metadata_ids:
                metadata = [file if int(file.site_ID) == x.site_ID else x for x in metadata]
            else:
                metadata.append(file)
            save_list_of_files_to_csv(metadata, CSV_OUTPUT_PATH)
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
            metadata = csv_to_audiofiledata_list(CSV_OUTPUT_PATH)
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
                save_list_of_files_to_csv(metadata, CSV_OUTPUT_PATH)
                # wait so as not to overload their poor servers
                time.sleep(SECONDS_BETWEEN_DOWNLOADS)

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
    metadata = csv_to_audiofiledata_list(CSV_OUTPUT_PATH)
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

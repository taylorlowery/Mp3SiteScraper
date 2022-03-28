import pytest
import SiteScraper


def test_single_page_scrape(test_session):
    test_id = 1
    with test_session:
        row = SiteScraper.scrape_single_page(test_session, test_id)
        # TODO: Some asserts maybe
        pass


def test_download_single_audio_file(test_session):
    test_id = 4725
    with test_session:
        row = SiteScraper.scrape_single_page(test_session, test_id)
        message, row = SiteScraper.download_file_from_page(test_session, row)
        # TODO: asserts
        pass

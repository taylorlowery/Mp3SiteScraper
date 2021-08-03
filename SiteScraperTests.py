import pytest
import SiteScraper

# unit tests

# clean html element
def test_clean_html_contents_NoInputReturnsEmptyString():
    retval = SiteScraper.clean_html_contents(None)
    assert retval == ''


def test_clean_html_contents_RemovesReturnCarriage():
    retval = SiteScraper.clean_html_contents('in\rput')
    assert retval == 'input'


def test_clean_html_contents_RemovesNewLine():
    retval = SiteScraper.clean_html_contents('\ninput\n')
    assert retval == 'input'


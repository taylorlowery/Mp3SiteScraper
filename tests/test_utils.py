import pytest
from utils import Utilities


# clean html element
def test_clean_html_contents_NoInputReturnsEmptyString():
    retval = Utilities.clean_html_contents(None)
    assert retval == ''


def test_clean_html_contents_RemovesReturnCarriage():
    retval = Utilities.clean_html_contents('in\rput')
    assert retval == 'input'


def test_clean_html_contents_RemovesNewLine():
    retval = Utilities.clean_html_contents('\ninput\n')
    assert retval == 'input'

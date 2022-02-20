import pytest

import SiteScraper


@pytest.fixture(scope="session")
def test_session():
    def _session():
        return SiteScraper.create_site_session()
    return _session()

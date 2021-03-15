import pytest
from notion_toolkit.notiorm.repo import *

def test_connection():
    Repo.init()

    assert Repo._client is not None
        
    page = Repo._client.get_block("https://www.notion.so/rafaba/0d78dbcba36841439f91bca25e35a92d?v=f79457d6b6a54c109315f79b3c9222b4")

    assert page.title == "References"

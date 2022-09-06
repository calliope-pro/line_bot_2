from typing import Tuple

import aiohttp
from bs4 import BeautifulSoup
from deta import _Base
from linebot.models.send_messages import TextSendMessage


async def request(url: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        html = await response.text()

    soup = BeautifulSoup(html, 'lxml')
    soup = BeautifulSoup(soup.select_one('.blog-post').text, 'lxml')
    contest_url_tag = soup.select_one('a:not(.username)')
    contest_url: str = contest_url_tag.get('href')
    contest_name: str = contest_url_tag.text
    return contest_name, contest_url

async def scrape():
    URL = 'https://atcoder.jp/?lang=ja'
    async with aiohttp.ClientSession() as session:
        response = await request(URL, session)
    return response

def create_message(response: Tuple[str, str], db: _Base):
    atcoder_contest_name, atcoder_contest_url = response
    if db.get(key='atcoder').get('name', None) != atcoder_contest_name:
        db.put(
            data={
                'name': atcoder_contest_name,
            },
            key='atcoder',
        )
        return f'{atcoder_contest_name}\n\n{atcoder_contest_url}'

    return None
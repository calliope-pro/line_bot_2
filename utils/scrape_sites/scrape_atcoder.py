import asyncio
import aiohttp
from bs4 import BeautifulSoup

URL = 'https://atcoder.jp/?lang=ja'

async def request(url: str, session: aiohttp.ClientSession):
    async with session.get(url) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'lxml')
        soup = BeautifulSoup(soup.select_one('.blog-post').text, 'lxml')
        contest_url_tag = soup.select_one('a:not(.username)')
        contest_url = contest_url_tag.get_attribute_list('href')[0]
        contest_name = contest_url_tag.text
        return contest_name, contest_url

async def scrape():
    async with aiohttp.ClientSession() as session:
        return await request(URL, session)

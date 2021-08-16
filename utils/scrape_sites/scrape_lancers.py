import asyncio
from typing import List, Set, Tuple
import aiohttp
from bs4 import BeautifulSoup

BASE_URL = 'https://www.lancers.jp/work/search?sort=client&type%5B%5D=competition&type%5B%5D=task&type%5B%5D=project&open=1&show_description=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=0&budget_from=5000&budget_to=&search=%E6%A4%9C%E7%B4%A2&keyword={}&not={}&page=1'
DETAIL_BASE_URL = 'https://www.lancers.jp/work/detail/{}'

KEY_WORDS:List[Tuple[str, str]] = [
    ('python', ''),
    ('React', '')
]

# headersを指定しないと403になるため
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
}

async def get_work_detail(work_url: str, session: aiohttp.ClientSession, key_word: str):
    '''
    案件のurlを基に案件url, 案件のカテゴリー, 案件の目標・内容の取得
    '''
    async with session.get(work_url, headers=HEADERS, ssl=True) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'lxml')
        work_category = soup.select_one('.c-definitionList:nth-of-type(1) > dd')
        work_purpose = soup.select_one('.c-definitionList:nth-of-type(2) > dd')
        return work_url, work_category.text.strip(), work_purpose.text.strip()


async def get_works(url: str, session: aiohttp.ClientSession, key_word: str=None):
    '''
    KEY_WORDによるurlに基づき案件のurl一覧を取得
    '''
    async with session.get(url, headers=HEADERS, ssl=True) as response:
        html = await response.text()
        soup = BeautifulSoup(html, 'lxml')
        work_urls = tuple(DETAIL_BASE_URL.format(soup_div.get_attribute_list('onclick')[0][-8:-1]) for soup_div in soup.select('div.c-media'))
        return await asyncio.gather(*(get_work_detail(work_url, session, key_word) for work_url in work_urls))


async def scrape():
    '''
    KEY_WORDSよりURLを正しくし、Lancersのスクレイピングを行う
    '''
    URLS = tuple(BASE_URL.format(*KEY_WORD) for KEY_WORD in KEY_WORDS)
    try:
        async with aiohttp.ClientSession() as session:
            result_works:List[List[Tuple[str, str]]] = await asyncio.gather(*(get_works(URL, session) for URL in URLS))
            return sum(result_works, []) # 次元を1つ落とす
    except Exception as e:
        print(e)
        print('-' * 60)

if __name__ == '__main__':
    # デバッグ用
    print(asyncio.get_event_loop().run_until_complete(scrape()))















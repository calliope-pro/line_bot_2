import asyncio
import re
from typing import List, Tuple

import aiohttp
from bs4 import BeautifulSoup
from deta import _Base

BASE_URL = "https://www.lancers.jp/work/search?sort=started&type%5B%5D=competition&type%5B%5D=task&type%5B%5D=project&open=1&show_description=1&work_rank%5B%5D=3&work_rank%5B%5D=2&work_rank%5B%5D=0&budget_from=&budget_to=&keyword={}&not={}&page={}"
DETAIL_BASE_URL = "https://www.lancers.jp/work/detail/{}"

# 検索したい語群と除外したい語群のリスト((検索したい語群,), (除外したい語群))
KEY_WORDS: List[Tuple[Tuple[str, ...], Tuple[str, ...]]] = [
    ("Django", ("ruby", "java")),
    (("React",), ("java", "php")),
    (("FastAPI",), tuple()),
    (("Deta",), ("Go",)),
]

# headers(User-Agent)を指定しないと403になるため
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like"
        " Gecko) Chrome/74.0.3729.169 Safari/537.36"
    )
}


async def get_work_detail(work_url: str, session: aiohttp.ClientSession):
    """
    urlを基に主にurl, 案件のカテゴリー, 案件の目標・内容のタプルを返す
    (※時々サイトの仕様によってズレる)
    """
    async with session.get(work_url, headers=HEADERS, ssl=True) as response:
        html = await response.text()
    soup = BeautifulSoup(html, "lxml")

    work_category = soup.select_one(".c-definitionList:nth-of-type(1) > dd") or ""
    work_purpose = soup.select_one(".c-definitionList:nth-of-type(2) > dd") or ""
    return work_url, work_category.text.strip(), work_purpose.text.strip()


async def get_works(url: str, session: aiohttp.ClientSession):
    """
    urlに基づき案件の詳細ページのurl一覧を取得し、並行スクレイピング
    """
    async with session.get(url, headers=HEADERS, ssl=True) as response:
        html = await response.text()
    soup = BeautifulSoup(html, "lxml")

    work_urls = (
        DETAIL_BASE_URL.format(re.sub(r"\D", "", soup_div.get("onclick")))
        for soup_div in soup.select('div.c-media[onclick^="goToLjpWorkDetail"]')
    )
    return await asyncio.gather(
        *(get_work_detail(work_url, session) for work_url in work_urls)
    )


async def scrape() -> Tuple[Tuple[str, str, str]]:
    """
    KEY_WORDSを基にURLを生成し、Lancersの並行スクレイピング
    """
    urls = (
        BASE_URL.format("+".join(key_word_pairs[0]), "+".join(key_word_pairs[1]), page)
        for key_word_pairs in KEY_WORDS
        for page in range(1, 4)
    )
    async with aiohttp.ClientSession() as session:
        jobs: Tuple[Tuple[Tuple[str, str, str]]] = await asyncio.gather(
            *(get_works(url, session) for url in urls)
        )
    return sum(jobs, [])  # 次元を1つ落とす


def create_message(jobs: Tuple[Tuple[str, str, str]], db: _Base):
    old_jobs_urls = set(db.get("jobs_urls").get("urls", []))

    diff_jobs_urls = set(job[0] for job in jobs).difference(old_jobs_urls)

    if diff_jobs_urls:
        db.put(data={"urls": [*old_jobs_urls, *diff_jobs_urls]}, key="jobs_urls")
        return "\n\n-------------------------------\n\n".join(
            map(lambda x: "\n・".join(x) if x[0] in diff_jobs_urls else "", jobs)
        )

    return None


if __name__ == "__main__":
    # デバッグ用
    print(asyncio.get_event_loop().run_until_complete(scrape()))

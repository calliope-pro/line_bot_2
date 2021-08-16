from pathlib import Path
from subprocess import CREATE_NO_WINDOW
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def start_browser(chromedriver_path: Path):
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled') # bot判定されない
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
    chrome_options.add_argument('--lang=ja')
    chrome_options.add_argument('--incognito') # シークレットモード
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument('--proxy-server="direct://"')
    # chrome_options.add_argument('--proxy-bypass-list=*')
    # chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) # chromeによるログの無効化
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) # 「自動テスト～によって制御されています」を消す
    chrome_options.add_experimental_option('useAutomationExtension', False) # chromeの拡張機能無効化
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 画像読み込み無効化
    service = Service(str(chromedriver_path))
    service.creationflags = CREATE_NO_WINDOW
    browser = webdriver.Chrome(options=chrome_options, service=service)
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    browser.implicitly_wait(1)
    return browser


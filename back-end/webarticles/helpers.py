from sys import settrace
from webarticles.models import WsjArticle, NytArticle, WsjStable, NytStable
from webarticles.serializers import WsjSerializer, NytSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pprint
pp = pprint.PrettyPrinter(indent=4)
import requests
from bs4 import BeautifulSoup
from rest_framework.decorators import api_view
from requests_html import HTMLSession
import threading
import queue
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.chrome.options import Options
from geotext import GeoText
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from fake_useragent import UserAgent
import random
from selenium.webdriver.common.keys import Keys
import pytz
            
def create_wsj_entries():
    print('checking if this logs')
    # drops the current table
    WsjArticle.objects.all().delete()

    # turns html content into soup
    html_content = get_wsj_world_html()
    soup = BeautifulSoup(html_content, "html.parser")
    
    # fires off archive req of top web article
    top_article = soup.select('h2.WSJTheme--headline--unZqjb45.reset.WSJTheme--heading-1--38k38q8O.typography--serif-display--ZXeuhS5E')
    a = top_article[0].contents[0]
    top_instance = WsjArticle()
    top_instance.title = a.getText()
    top_instance.link = a['href']
    archive_save(a['href'])

    # fires off rest of web article archive reqs
    articles = soup.select('h3.WSJTheme--headline--unZqjb45.reset.WSJTheme--heading-3--2z_phq5h.typography--serif-display--ZXeuhS5E')
    for b in articles:
        x = b.contents[0]
        link = x['href']
        archive_save(link)

    # goes back and scrapes the articles this time
    top_instance.full, top_instance.entity = scrape_archived_wsj(a['href'])
    top_instance.save()
    
    for b in articles:
        x = b.contents[0]
        title = x.getText()
        instance = WsjArticle()
        instance.title = title
        instance.link = x['href']
        instance.full, instance.entity = scrape_archived_wsj(x['href'])               
        instance.save()
    
    # updating the stable table if there is more than one article
    if len(WsjArticle.objects.all()) > 0:
        WsjStable.objects.all().delete()

        # Get all rows from the original table
        articles = WsjArticle.objects.all().values()

        # Iterate through the rows and create new rows in the stable table
        for article in articles:
            WsjStable.objects.create(**article)

def create_nyt_entries():
    # drops the current table
    NytArticle.objects.all().delete()

    # SETTING UP SELENIUM DRIVER AND FETCHING ARTICLES FROM NYT WORLD
    options = webdriver.ChromeOptions()
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_extension('/Users/gauravvarma/2023/project-optic/back-end/NopeCHA-CAPTCHA-Solver.crx')
    
    driver = webdriver.Chrome(executable_path='/path/to/chrome', options=options)
    driver.implicitly_wait(2000)
    driver.get('https://nopecha.com/setup#I-8CPW5LR1BBKH')
    driver.refresh()
    
    pst = pytz.timezone('America/Los_Angeles')
    driver.get(f'https://www.nytimes.com/issue/todayspaper/{datetime.now(pst).strftime("%Y/%m/%d")}/todays-new-york-times')

    intl_section = driver.find_element(By.XPATH, '//*[@id="collection-todays-new-york-times"]/div[1]/section[2]/ol')
    articles = intl_section.find_elements(By.TAG_NAME, 'a')

    for article in articles:
        href = article.get_attribute("href")
        archive_save(href)
    
    for article in articles:
        href = article.get_attribute("href")
        scrape_archived_nyt(href)
    
    # updating the stable table if there is more than one article
    if len(NytArticle.objects.all()) > 0:
        NytStable.objects.all().delete()
        
        # Get all rows from the original table
        articles = NytArticle.objects.all().values()

        # Iterate through the rows and create new rows in the stable table
        for article in articles:
            NytStable.objects.create(**article)
    
# fetches html from webpage
def get_wsj_world_html():
    # using requests and beautfil soup to scrape the view source
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
    LANGUAGE = "en-US,en;q=0.5"
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    
    pst = pytz.timezone('America/Los_Angeles')
    html_content = session.get(f'https://www.wsj.com/print-edition/{datetime.now(pst).strftime("%Y%m%d")}/world').text
    
    soup = BeautifulSoup(html_content, "html.parser")
    top_article = soup.select('h2.WSJTheme--headline--unZqjb45.reset.WSJTheme--heading-1--38k38q8O.typography--serif-display--ZXeuhS5E')
    if (len(top_article) == 0):
        return get_wsj_world_html()
        
    return html_content

def scrape_archived_wsj(url):
    # set up selenium and go to archive.ph
    options = webdriver.ChromeOptions()
    options = Options()
    
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_extension('/Users/gauravvarma/2023/project-optic/back-end/NopeCHA-CAPTCHA-Solver.crx')
    driver = webdriver.Chrome(executable_path='/path/to/chrome', options=options)
    driver.get('https://nopecha.com/setup#I-8CPW5LR1BBKH')
    driver.refresh()
    
    driver.implicitly_wait(100)
    driver.get('https://archive.ph/')
    
    # enter in article url...
    search_box = driver.find_element(By.XPATH, '//*[@style="padding:0px 2px;height:2em;width:100%;border:0"]')
    search_box.send_keys(url)
    print('keys submitted')
    
    # ...and hit save button
    search_button = driver.find_element(By.XPATH, '//*[@style="padding:4px;height:2em;width:100px"]')
    search_button.submit()
    print('search button submitted')
    
    # potential captcha here, so implicitly wait until archived page loads 
    refresh_signal = driver.find_element(By.XPATH, '//*[@style="margin:0;background-color:#EEEEEE"]')
    print('page refreshed')
    
    # scrape the wsj article
    paragraphs = driver.find_elements(By.XPATH, '//*[@style="color:rgb(51, 51, 51);font-family:Exchange, Georgia, serif;font-size:17px;font-weight:400;display:block;line-height:27px;margin-block-end:16px;margin-block-start:0px;margin-bottom:16px;margin-inline-end:10px;margin-inline-start:10px;margin-left:10px;margin-right:10px;margin-top:0px;padding-bottom:0px;padding-left:0px;padding-right:0px;padding-top:0px;"]')
    article = ''
    article += driver.find_element(By.XPATH, '//*[@id="main"]/div[1]/h1').text
    sub_title = driver.find_element(By.XPATH, '//*[@id="main"]/div[1]/h2').text
    article += f' {sub_title}'

    for paragraph in paragraphs:
        article += f' {paragraph.text}'
    
    # construct country dictionary
    article_data = GeoText(article)
    country_dict = article_data.country_mentions
    words = article.split()
    if 'US' not in country_dict:
        country_dict['US'] = 0
    country_dict['US'] += words.count('U.S.')
    
    if 'GB' not in country_dict:
        country_dict['GB'] = 0
    country_dict['GB'] += words.count('U.K.')
        
    # pick top 3 countries
    items = list(country_dict.items())
    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
    
    entities = []
    
    for key, value in sorted_items:
        if value >= 5:
            entities.append(key)

    return article, entities 

def scrape_archived_nyt(url):
    # starting up webdriver...
    options = webdriver.ChromeOptions()
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_extension('/Users/gauravvarma/2023/project-optic/back-end/NopeCHA-CAPTCHA-Solver.crx')
    driver = webdriver.Chrome(executable_path='/path/to/chrome', options=options)
    # ...installing nopecha, routing to archive.ph
    driver.get('https://nopecha.com/setup#I-8CPW5LR1BBKH')
    driver.refresh()
    driver.get('https://archive.ph/')
    driver.implicitly_wait(200)
    
    # at archive.ph, entering url and hitting save button
    search_box = driver.find_element(By.XPATH, '//*[@style="padding:0px 2px;height:2em;width:100%;border:0"]')
    search_box.send_keys(url)
    search_button = driver.find_element(By.XPATH, '//*[@style="padding:4px;height:2em;width:100px"]')
    search_button.submit()
    print('search button clicked, waiting to scrape')
    
    # potential captcha here, so implicitly wait until archived page loads 
    refresh_signal = driver.find_element(By.XPATH, '//*[@style="margin:0;background-color:#EEEEEE"]')
    print('popup located, proceeding to scrape')

    driver.refresh()

    try:
        # checking to see if standard title is there
        std_title = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@data-testid=\'headline\']')))
        print('found the title')
        
        # if so carry on to scrape the standard article
        std_title = driver.find_element(By.XPATH, '//*[@data-testid=\'headline\']').text
        instance = NytArticle()
        instance.title = std_title
        instance.link = url

        # Constructing full_text: first adding the title...
        full_text = std_title        
        full_text += ' '
        # ...then the subtitle...
        full_text = driver.find_element(By.XPATH, '//*[contains(@style,\'font-family:nyt-cheltenham, georgia, "times new roman", times, serif;font-size:23px;font-stretch:100%;font-style:normal;font-variant-caps:normal;font-variant-east-asian:normal;font-variant-ligatures:normal;font-variant-numeric:normal\')]').text
        
        full_text += ' '
        print('found the subtitle')

        # ...finally the paragraphs (xpath)
        paragraphs = driver.find_elements(By.XPATH, '//*[contains(@style,\'color:rgb(54, 54, 54);font-family:nyt-imperial, georgia, "times new roman", times, serif;font-size:20px;font-stretch:100%;font-style:normal;font-variant-caps:normal;font-variant-east-asian:normal;font-variant-ligatures:normal;font-variant-numeric:normal;font-weight:400;border-bottom-color:rgb(54, 54, 54);border-bottom-style:none;border-bottom-width:0px;border-image-outset:0;border-image-repeat:stretch;border-image-slice:100%;border-image-source:none;border-image-width:1;border-left-color:rgb(54, 54, 54);border-left-style:none;border-left-width:0px;border-right-color:rgb(54, 54, 54);border-right-style:none;border-right-width:0px;border-top-color:rgb(54, 54, 54);border-top-style:none;border-top-width:0px;display:block;line-height:30px;margin-block-end:15px;margin-block-start:0px;margin-bottom:15px;margin-inline-end:0px;margin-inline-start:0px;margin-left:0px;margin-right:0px;margin-top:0px;max-width:100%;overflow-wrap:break-word;padding-bottom:0px;padding-left:0px;padding-right:0px;padding-top:0px;text-size-adjust:100%;vertical-align:baseline;width:100%;\')]')
        print('found the paragraphs')

        for p in paragraphs:
            full_text += f' {p.text}'
        
        # CONSTRUCTING COUNTRY DICTIONARY
        article_data = GeoText(full_text)
        country_dict = article_data.country_mentions
        words = full_text.split()
        
        if 'US' not in country_dict:
            country_dict['US'] = 0
        country_dict['US'] += words.count('U.S.')
        
        if 'GB' not in country_dict:
            country_dict['GB'] = 0
        country_dict['GB'] += words.count('U.K.')
        
        # saving countries with at least 5 mentions
        # creating list of tuples to sort dictionary by mention rate
        items = list(country_dict.items())
        sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
        
        entities = []
        
        for key, value in sorted_items:
            if value >= 5:
                entities.append(key)
                
        instance.entity = entities
        instance.full = full_text
        instance.save()
        
    except:
        # if standard title isn't there, check to see if the 'hero' title is
        try:
            hero_title = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="fullBleedHeaderContent"]/header')))

            # if hero title is there then proceed to scrape article
            hero_title = driver.find_element(By.XPATH, '//*[@id="fullBleedHeaderContent"]/header').text
            instance = NytArticle()
            instance.title = hero_title
            instance.link = url
            
            # Adding the title... 
            full_text = instance.title
            # ...and subtitle to the full text...
            full_text += ' '
            full_text = driver.find_element(By.XPATH, '//*[@id="fullBleedHeaderContent"]/header/div[2]/div[3]').text
            
            # ...abd finally the paragraphs (xpath)
            full_text += ' '
            paragraphs = driver.find_elements(By.XPATH, '//*[contains(@style,\'color:rgb(54, 54, 54);font-family:nyt-imperial, georgia, "times new roman", times, serif;font-size:20px;font-stretch:100%;font-style:normal;font-variant-caps:normal;font-variant-east-asian:normal;font-variant-ligatures:normal;font-variant-numeric:normal;font-weight:400;border-bottom-color:rgb(54, 54, 54);border-bottom-style:none;border-bottom-width:0px;border-image-outset:0;border-image-repeat:stretch;border-image-slice:100%;border-image-source:none;border-image-width:1;border-left-color:rgb(54, 54, 54);border-left-style:none;border-left-width:0px;border-right-color:rgb(54, 54, 54);border-right-style:none;border-right-width:0px;border-top-color:rgb(54, 54, 54);border-top-style:none;border-top-width:0px;display:block;line-height:30px;margin-block-end:15px;margin-block-start:0px;margin-bottom:15px;margin-inline-end:0px;margin-inline-start:0px;margin-left:0px;margin-right:0px;margin-top:0px;max-width:100%;overflow-wrap:break-word;padding-bottom:0px;padding-left:0px;padding-right:0px;padding-top:0px;text-size-adjust:100%;vertical-align:baseline;width:100%;\')]')

            for p in paragraphs:
                full_text += f' {p.text}'
            
            # CONSTRUCTING COUNTRY DICTIONARY
            article_data = GeoText(full_text)
            country_dict = article_data.country_mentions
            words = full_text.split()
            
            if 'US' not in country_dict:
                country_dict['US'] = 0
            country_dict['US'] += words.count('U.S.')
            
            if 'GB' not in country_dict:
                country_dict['GB'] = 0
            country_dict['GB'] += words.count('U.K.')
                
            # saving countries with at least 5 mentions
            # creating list of tuples to sort dictionary by mention rate
            items = list(country_dict.items())
            sorted_items = sorted(items, key=lambda x: x[1], reverse=True)
            
            entities = []
            
            for key, value in sorted_items:
                if value >= 5:
                    entities.append(key)
                    
            instance.entity = entities
            instance.full = full_text
            instance.save()
        
        except:
            # and finally if neither std nor hero title is there, then skip this article...
            # ... will handle edge case later (re: live news) + other one about front page world news
            return

def archive_save(url):
     # starting up web driver... 
    options = webdriver.ChromeOptions()
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_extension('/Users/gauravvarma/2023/project-optic/back-end/NopeCHA-CAPTCHA-Solver.crx')
    driver = webdriver.Chrome(executable_path='/path/to/chrome', options=options)
    # ...setting up nopecha
    driver.get('https://nopecha.com/setup#I-8CPW5LR1BBKH')
    driver.refresh()
    #  ...and routing to archive.ph
    driver.implicitly_wait(200)
    driver.get('https://archive.ph/')
    
    # entering in article url...
    search_box = driver.find_element(By.XPATH, '//*[@style="padding:0px 2px;height:2em;width:100%;border:0"]')
    search_box.send_keys(url)
    # ...and submiting the search button
    search_button = driver.find_element(By.XPATH, '//*[@style="padding:4px;height:2em;width:100px"]')
    search_button.submit()
    
    # wait until the proper url is hit:
    # this ensures that nopecha is given enough time to solve the captcha
    wait = WebDriverWait(driver, 200).until(EC.url_contains("archive.ph/"))
    
    return


from sys import settrace
from webarticles.models import WsjArticle, NytArticle, WsjStable, NytStable
from webarticles.serializers import WsjSerializer, NytSerializer, WsjStableSerializer, NytStableSerializer
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
from .helpers import create_nyt_entries, create_wsj_entries

# sends back webarticles table to front end
class WsjList(APIView):
    def get(self, request, format=None):
        web_articles = WsjStable.objects.all()
        serializer = WsjStableSerializer(web_articles, many=True)
        return Response(serializer.data)

class NytList(APIView):
    def get(self, request, format=None):
        web_articles = NytStable.objects.all()
        serializer = NytStableSerializer(web_articles, many=True)
        return Response(serializer.data)

# creates entries in tables
@api_view(('GET',))
def wall_street_journal(request):
    create_wsj_entries()
    return Response("Latest Data Fetched from The Wall Street Journal")

@api_view(('GET',))
def new_york_times(request):
    create_nyt_entries()
    return Response("Latest Data Fetched from The New York Times")

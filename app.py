from flask import Flask, render_template, redirect, url_for, request, session
import requests
import os
import json
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
import random

app = Flask(__name__)

def get_google_search():
    imgs = []
    url = "https://www.googleapis.com/customsearch/v1?key=AIzaSyDJSiDFD4sqNCFt680gAOsPfDbgI8Lxq9I&cx=0740ab079404c4f48&q=namjoon&searchType=image"
    response = requests.get(url)
    html = response.content
    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")
    my_json = soup.decode('utf8').replace("'", '"')
    data = json.loads(my_json)
    for img in data["items"]:
        imgs.add(img["link"])
    return imgs

def duck_duck_go():
    imgs = []
    params = {
    "engine": "duckduckgo",
    "q": "namjoon",
    "api_key": "280be8e2dc88b7f74ea5e1e4c2f24ec73b141a25c5a55810ae776172e141da06"
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    inline_images = results["inline_images"]
    for img in inline_images:
        imgs.add(img["image"])
    return imgs

def kpopping():
    imgs = []
    url = "https://kpopping.com/kpics/gender-all/category-all/idol-RM/group-any/order"
    response = requests.get(url)
    html = response.content

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")
    imgs = soup.find_all("div", {"class": "cell"})
    for img in imgs:
    children = img.findChildren("img")
    for child in children:
        child['src'] = child['src'].replace("300", "800")
        url = "https://kpopping.com" + child['src'].split("?")[0]
        imgs.add(url)
    return imgs


@app.route('/')
def login():
    all_imgs = []
    google = get_google_search()
    ddg = duck_duck_go()
    kpop = kpopping()
    all_imgs.extend(google)
    all_imgs.extend(ddg)
    all_imgs.extend(kpop)
    index = random.randint(0, len(all_imgs)-1)
    return render_template('index.html', namjoon=all_imgs[index])
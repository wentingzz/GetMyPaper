
# coding: utf-8

# In[10]:


import urllib
import requests
from bs4 import BeautifulSoup
import time
import codecs
import logging
import re
    
# This function is to get the doi of the articles in the page
def download_pdf(doi, name):
    raw = requests.get("https://sci-hub.tw/" + doi, allow_redirects = False)
    soup = BeautifulSoup(raw.text)
    frame = soup.find(id="pdf")
    try:
        if 'https:' in frame['src']:
            urllib.request.urlretrieve(frame['src'], name)
        else:
            urllib.request.urlretrieve("https:" + frame['src'], name)
#         logging.info("Downloaded %s with doi (%s)", name, doi) 
    except:
        logging.warning(doi + " cannot be downloaded because file not found by the doi or Sci-Hub is blocked")


delimiter = ")("
headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'referrer': 'https://google.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Pragma': 'no-cache',
}

def rename(authors, journal, year, article):
    for i in range(0, len(authors)):
        authors[i] = authors[i].split(" ")[-1]
    name = "_".join(["_".join(authors), journal, year, article])
    name = re.sub('[^a-zA-Z0-9_\-\.]', ',', name) 
    return name + ".pdf"


def search_jcr(key, page):
    html = requests.get("https://academic.oup.com/jcr/search-results?page=1&q=" + key +"&fl_SiteID=5397&SearchSourceType=1&allJournals=" + page,headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("div", "sr-list al-article-box al-normal clearfix"):
        title = link.find("h4", "sri-title customLink al-title").text.replace("\n", "")
        title = "_".join(title.split())
        authors = link.find("div", "sri-authors al-authors-list")
        if authors is None:
            continue
        else:
            authors = authors.text.split(",")
        year = link.find("div", "sri-date al-pub-date").text[-4:]
        download_name = rename(authors, 'JCR', year, title)
        doi = link.find("a", href=lambda href: href and "doi.org" in href).text.replace("https://doi.org/", "")
#         print(download_name, doi)
#         download_pdf(doi, download_name)


def search_wiley(key, page):
    html = requests.get("https://onlinelibrary.wiley.com/action/doSearch?AllField=" + key + "&SeriesKey=15327663&pageSize=20&startPage=" + page, headers=headers)
#     print("https://onlinelibrary.wiley.com/action/doSearch?AllField=" + key + "&SeriesKey=15327663&pageSize=20&startPage=" + page)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("li", class_="clearfix separator search__item exportCitationWrapper"):
        item = link.find("a", "publication_title visitable")
        title = "_".join(item.text.replace("\n", "").split())
        authors = link.find("ul", "meta__authors rlist--inline comma")
        if authors is None:
            continue
        else:
            authors = authors.text.replace("\n", ",")
            authors = re.sub("\s\s\s+", "", authors)
            if authors[0] == ",": authors = authors[1:]
            if authors[-1] == ",": authors = authors[:-1]
            authors = authors.split(",")
        year = link.find("p", "meta__epubDate").text.replace(" ", "").replace("\n", "")[-4:]
        download_name = rename(authors, "WOL", year, title)
        doi = item.get("href").split("doi/")[-1]
#         download_pdf(doi, download_name)

logging.basicConfig(format='%(levelname)8s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

keyword = input("Enter the keyword you want to search: ")
# search_jcr(keyword, "1")
search_wiley(keyword, "1")

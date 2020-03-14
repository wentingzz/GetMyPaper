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
    if name[-1] == ".": name = name[:-1] 
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

def search_jams(key, page):
    html = requests.get("https://link.springer.com/search/page/"+ page + "?search-within=Journal&facet-journal-id=11747&query=" + key, headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find(id="results-list").find_all("li"):
        item = link.find("a", "title")
        title = "_".join(item.text.replace("\n", "").split())
        authors = link.find("span", "authors")
        if authors is None:
            continue
        else:
            authors = authors.text.replace("…", "").split(",")
        year = link.find("span", "year").text[-5:-1]
        download_name = rename(authors, 'JCR', year, title)
        doi = item.get("href").split("article/")[-1]
#         print(download_name, doi)
#         download_pdf(doi, download_name)


# def search_jpsp(key, page):
#     html = requests.get("https://www.apa.org/search?query=" + key + "&page="+ page, headers=headers)
#     soup = BeautifulSoup(html.text)

def search_gs(key, page):
    
    html = requests.get("https://scholar.google.com/scholar?start=" + str(10 * int(page) - 10) + "&q=" + key + "&hl=en&as_sdt=0,34", headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.findAll("div", "gs_ri"):
        title = link.find("h3", "gs_rt").find("a").text.replace("\n", "")
        title = "_".join(title.split())
        item = link.find("div", "gs_a")
        if item is None:
            continue
        else:
            item = item.text.split("-")
            authors = item[0].split(",")
            year = item[1][-5:-1]
        download_name = rename(authors, 'GS', year, title)
        print(download_name)
#         doi = item.get("href").split("article/")[-1]

def search_wiley(key, page, series, journal):
    html = requests.get("https://onlinelibrary.wiley.com/action/doSearch?AllField=" + key + "&SeriesKey=" + series + "&pageSize=20&startPage=" + page, headers=headers)
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
        download_name = rename(authors, journal, year, title)
        doi = item.get("href").split("doi/")[-1]
        print(download_name, doi)
#         download_pdf(doi, download_name)

def search_jcp_w(key, page):
    search_wiley(key, page, "15327663", "JCP")

def search_pm(key, page):
    search_wiley(key, page, "15206793", "PM")

def search_sagepub(key, page, series, journal):
    html = requests.get("https://journals.sagepub.com/action/doSearch?filterOption=thisJournal&SeriesKey=" + series + "a&AllField=" + key + "&pageSize=20&startPage=" + page, headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("article", class_="searchResultItem"):
        item = link.find("a", attrs={"data-item-name":"click-article-title"})
        title = "_".join(item.text.replace("\n", "").split())
        temp = link.findAll("span", "contribDegrees")
        authors = []
        for t in temp:
            tmp = t.find("a")
            if tmp is not None:
                authors.append(tmp.text)
        if not authors:
            continue
        year = link.find("span", "maintextleft").text.replace(" ", "").replace("\n", "")[-5:-1]
        download_name = rename(authors, journal, year, title)
        doi = item.get("href").split("/doi/full/")[-1]
#         download_pdf(doi, download_name)
        print(download_name, doi)

def search_jm(key, page):
    search_sagepub(key, page, "jmx", "JM")

def search_jmr(key, page):
    search_sagepub(key, page, "mrj", "JMR")
    
def search_jppm(key, page):
    search_sagepub(key, page, "ppo", "JPPM")

def search_pubsonline(key, page, series, journal):
    html = requests.get("https://pubsonline.informs.org/action/doSearch?AllField=" + key + "&SeriesKey=mnsc" + series + "&pageSize=20&startPage=" + page, headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("div", class_="item__body"):
        item = link.find("h5", "hlFld-Title meta__title meta__title__margin").find("a")
        title = "_".join(item.text.replace("\n", "").split())
        authors = link.find("ul", "meta__authors rlist--inline")
        if authors is None:
            continue
        else:
            authors = authors.text.replace("\n", ",")
            authors = re.sub("\s\s\s+", "", authors)
            if authors[0] == ",": authors = authors[1:]
            if authors[-1] == ",": authors = authors[:-1]
            authors = authors.split(",")
        year = link.find("span", "publicationYear").text.replace(" ", "").replace("\n", "")[-5:-1]
        print(authors, title, year)
        download_name = rename(authors, journal, year, title)
        doi = item.get("href").split("doi/")[-1]
#         download_pdf(doi, download_name)
        print(download_name, doi)

def search_mks(key, page):
    search_pubsonline(key, page, "mks", "MKS")

def search_mgs(key, page):
    search_pubsonline(key, page, "mns", "MGS")


logging.basicConfig(format='%(levelname)8s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

keyword = input("Enter the keyword you want to search: ")
page = input("Enter the page you want to start: ")
# search_jcr(keyword, page)
# search_jcp_w(keyword, str(int(page) - 1))
# search_jm(keyword, str(int(page) - 1))
# search_jmr(keyword, str(int(page) - 1))
# search_jppm(keyword, str(int(page) - 1))

# NOT TESTED YET!!!!!!!!!!!
# search_mks(keyword, str(int(page) - 1))
# search_mgs(keyword, str(int(page) - 1))

# search_pm(keyword, page)
# search_jams(keyword, page)
# search_gs(keyword, page)
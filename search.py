import urllib
import gradio as gr

import requests
from bs4 import BeautifulSoup
import time
import codecs
import logging
import re
    
# This function is to get the doi of the articles in the page
def download_pdf(doi, name):
    url = "https://sci-hub.se/" + doi
    with requests.get(url, allow_redirects = False) as raw:
        # Check if the response status code is 301
        if raw.status_code == 301:
            # Get the new location from the response headers
            new_url = raw.headers['Location']
            # Send a new GET request to the new location
            raw = requests.get(new_url)
        soup = BeautifulSoup(raw.text, "html.parser")

        try:
            frame = soup.find(id="pdf")
            if 'https:' in frame['src']:
                urllib.request.urlretrieve(frame['src'], name)
            else:
                urllib.request.urlretrieve("https:" + frame['src'], name)
            #
            # if 'https:' in frame['src']:
            #     urllib.request.urlretrieve(frame['src'], name)
            # else:
            #     urllib.request.urlretrieve("https:" + frame['src'], name)
    #         logging.info("Downloaded %s with doi (%s)", name, doi)
        except Exception as e:
            logging.warning(e)
            logging.warning(url + " cannot be downloaded because file not found in Sci-Hub. Filename = " + name)


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
    with requests.get("https://academic.oup.com/jcr/search-results?page=" + page + "&q=" + key +"&fl_SiteID=5397&SearchSourceType=1&allJournals=1",headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
        for link in soup.find_all("div", "sr-list al-article-box al-normal clearfix"):
            title = link.find("h4", "sri-title customLink al-title")
            if title is None:
                title = link.find("h4", "sri-title customLink")

            title = "_".join(title.text.replace("\n", "").split())
            authors = link.find("div", "sri-authors al-authors-list")
            if authors is None:
                continue
            else:
                authors = authors.text.split(",")
            year = link.find("div", "sri-date al-pub-date").text[-4:]
            download_name = rename(authors, 'JCR', year, title)
            doi = link.find("a", href=lambda href: href and "doi.org" in href).text.replace("https://doi.org/", "")
            download_pdf(doi, download_name)

def search_jams(key, page):
    with requests.get("https://link.springer.com/search/page/"+ page + "?search-within=Journal&facet-journal-id=11747&query=" + key, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_wiley(key, page, series, journal):
    with requests.get("https://onlinelibrary.wiley.com/action/doSearch?AllField=" + key + "&SeriesKey=" + series + "&pageSize=20&startPage=" + page, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_jcp_w(key, page):
    search_wiley(key, page, "15327663", "JCP")

def search_pm(key, page):
    search_wiley(key, page, "15206793", "PM")

def search_sagepub(key, page, series, journal):
    with requests.get("https://journals.sagepub.com/action/doSearch?filterOption=thisJournal&SeriesKey=" + series + "a&AllField=" + key + "&pageSize=20&startPage=" + page, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_jm(key, page):
    search_sagepub(key, page, "jmx", "JM")

def search_jmr(key, page):
    search_sagepub(key, page, "mrj", "JMR")
    
def search_jppm(key, page):
    search_sagepub(key, page, "ppo", "JPPM")

def search_pubsonline(key, page, series, journal):
    url = "https://pubsonline.informs.org/action/doSearch?AllField=" + key + "&SeriesKey=" + series + "c&pageSize=20&startPage=" + page
    with requests.get(url, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
        for link in soup.find_all("div", class_="item__body"):
            item = link.find("h5", "hlFld-Title meta__title meta__title__margin").find("a")
            title = "_".join(item.text.replace("\n", "").split())
            authors = link.find("ul", "meta__authors rlist--inline").find_all("a", "entryAuthor linkable hlFld-ContribAuthor")
            if not authors:
                continue
            else:
                for i in range(len(authors)):
                    authors[i] = authors[i].text
                    authors[i] = re.sub("\s+$", "", authors[i])
            year = link.find("span", "publicationYear").text.replace(" ", "").replace("\n", "")[-5:-1]
            download_name = rename(authors, journal, year, title)
            doi = item.get("href").split("doi/")[-1]
            download_pdf(doi, download_name)

def search_mks(key, page):
    search_pubsonline(key, page, "mksc", "MKS")

def search_mgs(key, page):
    search_pubsonline(key, page, "mnsc", "MGS")


logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

keyword = input("Enter the keyword you want to search: ")
page = input("Enter the page you want to start: ")
for i in range(3):
    search_jcr(keyword, str(int(page) + i))
    search_jcp_w(keyword, str(int(page) + i - 1))
    search_jm(keyword, str(int(page) + i - 1))
    search_jmr(keyword, str(int(page) + i - 1))
    search_jppm(keyword, str(int(page) + i - 1))
    search_mks(keyword, str(int(page) + i - 1))
    search_mgs(keyword, str(int(page) + i - 1))
    search_pm(keyword, str(int(page) + i - 1))
    search_jams(keyword, str(int(page) + i ))
logging.info("Congrats! All the articles are downloaded! ")


    
# This function is to get the doi of the articles in the page
def download_pdf(doi, name):
    with requests.get("https://sci-hub.tw/" + doi, allow_redirects = False) as raw:
        soup = BeautifulSoup(raw.text)
        frame = soup.find(id="pdf")
        try:
            if 'https:' in frame['src']:
                urllib.request.urlretrieve(frame['src'], name)
            else:
                urllib.request.urlretrieve("https:" + frame['src'], name)
    #         logging.info("Downloaded %s with doi (%s)", name, doi) 
        except:
            logging.warning(doi + " cannot be downloaded because file not found in Sci-Hub. Filename = " + name)


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
    with requests.get("https://academic.oup.com/jcr/search-results?page=" + page + "&q=" + key +"&fl_SiteID=5397&SearchSourceType=1&allJournals=1",headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
        for link in soup.find_all("div", "sr-list al-article-box al-normal clearfix"):
            title = link.find("h4", "sri-title customLink al-title")
            if title is None:
                title = link.find("h4", "sri-title customLink")

            title = "_".join(title.text.replace("\n", "").split())
            authors = link.find("div", "sri-authors al-authors-list")
            if authors is None:
                continue
            else:
                authors = authors.text.split(",")
            year = link.find("div", "sri-date al-pub-date").text[-4:]
            download_name = rename(authors, 'JCR', year, title)
            doi = link.find("a", href=lambda href: href and "doi.org" in href).text.replace("https://doi.org/", "")
            download_pdf(doi, download_name)

def search_jams(key, page):
    with requests.get("https://link.springer.com/search/page/"+ page + "?search-within=Journal&facet-journal-id=11747&query=" + key, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_wiley(key, page, series, journal):
    with requests.get("https://onlinelibrary.wiley.com/action/doSearch?AllField=" + key + "&SeriesKey=" + series + "&pageSize=20&startPage=" + page, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_jcp_w(key, page):
    search_wiley(key, page, "15327663", "JCP")

def search_pm(key, page):
    search_wiley(key, page, "15206793", "PM")

def search_sagepub(key, page, series, journal):
    with requests.get("https://journals.sagepub.com/action/doSearch?filterOption=thisJournal&SeriesKey=" + series + "a&AllField=" + key + "&pageSize=20&startPage=" + page, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
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
            download_pdf(doi, download_name)

def search_jm(key, page):
    search_sagepub(key, page, "jmx", "JM")

def search_jmr(key, page):
    search_sagepub(key, page, "mrj", "JMR")
    
def search_jppm(key, page):
    search_sagepub(key, page, "ppo", "JPPM")

def search_pubsonline(key, page, series, journal):
    url = "https://pubsonline.informs.org/action/doSearch?AllField=" + key + "&SeriesKey=" + series + "c&pageSize=20&startPage=" + page
    with requests.get(url, headers=headers) as html:
        soup = BeautifulSoup(html.text, "html.parser")
        for link in soup.find_all("div", class_="item__body"):
            item = link.find("h5", "hlFld-Title meta__title meta__title__margin").find("a")
            title = "_".join(item.text.replace("\n", "").split())
            authors = link.find("ul", "meta__authors rlist--inline").find_all("a", "entryAuthor linkable hlFld-ContribAuthor")
            if not authors:
                continue
            else:
                for i in range(len(authors)):
                    authors[i] = authors[i].text
                    authors[i] = re.sub("\s+$", "", authors[i])
            year = link.find("span", "publicationYear").text.replace(" ", "").replace("\n", "")[-5:-1]
            download_name = rename(authors, journal, year, title)
            doi = item.get("href").split("doi/")[-1]
            download_pdf(doi, download_name)

def search_mks(key, page):
    search_pubsonline(key, page, "mks", "MKS")

def search_mgs(key, page):
    search_pubsonline(key, page, "mns", "MGS")


logging.basicConfig(format='%(levelname)s: %(message)s')
logging.getLogger().setLevel(logging.INFO)
def search_journals(keyword, page, output_folder):
    for i in range(3):
        search_jcr(keyword, str(int(page) + i))
        search_jcp_w(keyword, str(int(page) + i - 1))
        search_jm(keyword, str(int(page) + i - 1))
        search_jmr(keyword, str(int(page) + i - 1))
        search_jppm(keyword, str(int(page) + i - 1))
        search_mks(keyword, str(int(page) + i - 1))
        search_mgs(keyword, str(int(page) + i - 1))
        search_pm(keyword, str(int(page) + i - 1))
        search_jams(keyword, str(int(page) + i ))
    logging.info("Congrats! All the articles are downloaded! ")


# iface = gr.Interface(
#     fn=search_journals,
#     inputs=[
#         gr.inputs.Textbox(lines=1, label="Enter the keyword you want to search"),
#         gr.inputs.Textbox(lines=1, label="Enter the page you want to start"),
#         gr.inputs.File(label="Select your output folder", type="folder")
#     ],
#     outputs="text",
#     title="Journal Searcher",
#     server_port=8080
# )
#
# iface.launch(share=True)
keyword = input("Enter the keyword you want to search: ")
page = input("Enter the page you want to start: ")

search_journals(keyword, page, "")
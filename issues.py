
# In[58]:


import urllib.request
import requests
import time
from bs4 import BeautifulSoup, Comment
import datetime
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

headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'referrer': 'https://google.com',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Pragma': 'no-cache',
}
delimiter = ")("

def rename(authors, journal, year, article):
    for i in range(0, len(authors)):
        authors[i] = authors[i].split(" ")[-1]
    name = "_".join(["_".join(authors), journal, year, article])
    name = re.sub('[^a-zA-Z0-9_\-\.]', '-', name) 
    return name + ".pdf"

def issue_wiley(url):
    html = requests.get("https://onlinelibrary.wiley.com" + url, headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("div", 'issue-item'):
        title = link.find("h2").text.replace(" ", "_")
        authors = link.findAll("span", class_="author-style")
        if not authors:
            continue
        else:
            for i in range(0, len(authors)):
                authors[i] = authors[i].text.replace("\n ", "")
        year = link.findAll("span", tabindex="0")[-1].text[-4:]
        download_name = rename(authors, "WOL", year, title)
        doi = link.find("a", class_="issue-item__title visitable").get("href").replace("/doi/", "")
        print(download_name)
#         download_pdf(doi, download_name)

def issue_jcr(url):
    html = requests.get("https://academic.oup.com"+ url, headers=headers)
    soup = BeautifulSoup(html.text)
    for link in soup.find_all("div", 'al-article-items'):
        title = link.find('h5', "customLink item-title").find("a").text.replace(" ", "_")
        authors = link.findAll("a", href=lambda href: href and "/jcr/search-results?f_Authors" in href)
        if not authors:
            continue
        else:
            for i in range(0, len(authors)):
                authors[i] = authors[i].text
        year = link.find("div", "ww-citation-primary").text.split(", ")[3][-4:]
        download_name = rename(authors, "JCR", year, title)
        print(download_name)
        doi = link.find("a", href=lambda href: href and "doi.org" in href).get('href').replace("https://doi.org/", "")
#         download_pdf(doi, download_name)

def issue_sd(vol, issue):
    html = requests.get("https://www.sciencedirect.com/journal/journal-of-consumer-psychology/vol/"+ vol + "/issue/" + issue, headers=headers)
    soup = BeautifulSoup(html.text)
    year = soup.find("h3", "js-issue-status text-s").text[-5:-1]
    for link in soup.find_all("li", 'js-article-list-item article-item u-padding-xs-top u-margin-l-bottom'):
        title = link.find("a", "anchor article-content-title u-margin-xs-top u-margin-s-bottom").text.replace(" ", "_")
        authors = link.find("div", "text-s u-clr-grey8 js-article__item__authors")
        if authors is None:
            continue
        else:
            authors = authors.text.split(", ")
        download_name = rename(authors, "SD", year, title)
        doi = link.find("div", text=lambda text: text and "doi.org" in text).text.split("doi.org/")[1]
        print(download_name)
#         download_pdf(doi, download_name)
    
logging.basicConfig(format='%(levelname)8s: %(message)s')
logging.getLogger().setLevel(logging.INFO)


in_str = input("Enter the volumes want to download the issues (1-27): ")
temp = re.findall(r'\d+', in_str)
for vol in range(int(temp[0]), int(temp[1]) + 1):
    for issue in range(1, 5):
        print("VOL %s ISSUE %s", str(vol), str(issue))
        issue_sd(str(vol), str(issue))

# in_str = input("Enter the period want to download the issues (1990-2020): ")
# temp = re.findall(r'\d+', in_str) 
# for year in range(int(temp[0]), int(temp[1]) + 1):
#     html = requests.get("https://academic.oup.com/jcr/issue-archive/" + str(year), headers=headers)
#     soup = BeautifulSoup(html.text)
#     for issue in soup.findAll("div", "customLink"):
#         issue_jcr(issue.find("a").get("href"))


# for year in range(int(temp[0]), int(temp[1]) + 1):
#     html = requests.get("https://onlinelibrary.wiley.com/loi/15327663/year/" + str(year), headers=headers)
#     soup = BeautifulSoup(html.text)
#     for issue in soup.findAll("a", "visitable"):
#         issue_wiley(issue.get("href"))

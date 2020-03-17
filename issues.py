import urllib.request
import requests
import time
from bs4 import BeautifulSoup, Comment
import datetime
import logging
import re

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

def issues_jams(start, end):
    with requests.get("https://link.springer.com/journal/11747/volumes-and-issues", headers=headers) as html:
        soup = BeautifulSoup(html.text)
        for vol in soup.findAll("ul", "c-list-group c-list-group--bordered c-list-group--md u-mb-16"):
            vol_num = -1
            for issue in vol.findAll("a", "u-interface-link u-text-sans-serif u-text-sm"):
                vol_num = int(issue.get("href").split("/")[-2])
                if vol_num > end:
                    break
                issue_jams(issue.get("href"))
            if vol_num <= start:
                break
    logging.info("Finished issues in JAMS")

def issue_jams(url):
    with requests.get("https://link.springer.com" + url, headers=headers) as html:
        soup = BeautifulSoup(html.text)
        for link in soup.findAll("div", "toc-item"):
            item = link.find("h3", "title").find("a")
            title = item.text.replace(" ", "_")
            authors = link.find("span", class_="authors").findAll("a")
            if not authors:
                continue
            else:
                for i in range(0, len(authors)):
                    authors[i] = authors[i].text.replace("\n ", "")
            with requests.get("https://link.springer.com/" + item.get("href"), headers=headers) as tmp_html:
                tmp_soup = BeautifulSoup(tmp_html.text)
                year = tmp_soup.find("a", {"data-track-action":"publication date"}).text[-4:]
            download_name = rename(authors, "JAMS", year, title)
            doi = item.get("href").replace("/article/", "")
            download_pdf(doi, download_name)


def issue_jcr(url):
    with requests.get("https://academic.oup.com"+ url, headers=headers) as html:
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
            doi = link.find("a", href=lambda href: href and "doi.org" in href).get('href').replace("https://doi.org/", "")
            download_pdf(doi, download_name)

def issue_wiley(url, journal):
    with requests.get("https://onlinelibrary.wiley.com" + url, headers=headers) as html:
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
            download_name = rename(authors, journal, year, title)
            doi = link.find("a", class_="issue-item__title visitable").get("href").replace("/doi/", "")
            download_pdf(doi, download_name)

def issue_sagepub(url, journal, year):
    with requests.get(url, headers=headers) as html:
        soup = BeautifulSoup(html.text)
        for link in soup.findAll("table", "articleEntry"):
            authors = link.findAll("span", "contribDegrees")
            if not authors:
                continue
            else:
                for i in range(0, len(authors)):
                    authors[i] = authors[i].find("a").text.replace("\n ", "")
            title = link.find("h3", "heading-title").text.replace(" ", "_")
            download_name = rename(authors, journal, year, title)
            doi = link.find("a", {"data-item-name":"click-article-title"}).get("href").replace("/doi/full/", "")
            download_pdf(doi, download_name)

def issues_jm(start_year, end_year):
    for year in range(start_year, end_year + 1):
        print("https://journals.sagepub.com/loi/JMX?year=" + str(year))
        with requests.get("https://journals.sagepub.com/loi/JMX?year=" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("div", "row js_issue"):
                issue_sagepub(issue.find("a").get("href"), "JM", str(year))
    logging.info("Finished issues in JM")
    
def issues_jppm(start_year, end_year):
    for year in range(start_year, end_year + 1):
        with requests.get("https://journals.sagepub.com/loi/ppoa?year=" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("div", "row js_issue"):
                issue_sagepub(issue.find("a").get("href"), "JPPM", str(year))
    logging.info("Finished issues in JPPM")
            
def issues_jmr(start_year, end_year):
    for year in range(start_year, end_year + 1):
        with requests.get("https://journals.sagepub.com/loi/mrja?year=" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("div", "row js_issue"):
                issue_sagepub(issue.find("a").get("href"), "JMR", str(year))
    logging.info("Finished issues in JMR")            

def issue_pubsonline(url, year, journal):
    with requests.get(url, headers=headers) as html:
        soup = BeautifulSoup(html.text)

        for link in soup.findAll("div", "issue-item"):
            authors = link.findAll("a", "entryAuthor linkable hlFld-ContribAuthor")
            if not authors:
                continue
            else:
                for i in range(0, len(authors)):
                    authors[i] = authors[i].text.replace("\n ", "")
                    authors[i] = re.sub("\s+$", "", authors[i])
            item = link.find("h5", "issue-item__title").find("a")
            title = item.text.replace(" ", "_")
            download_name = rename(authors, journal, year, title)
            doi = item.get("href").replace("/doi/abs/", "")
            download_pdf(doi, download_name)


def issues_mgs(start_year, end_year):
    for year in range(start_year, end_year + 1):
        with requests.get("https://pubsonline.informs.org/loi/mnsc/group/d" + str(year//10 * 10) + ".y" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for link in soup.findAll("a", "issue-info__vol-issue"):
                issue_pubsonline("https://pubsonline.informs.org" + link.get("href"), str(year), "MGS")
    logging.info("Finished issues in MGS")

def issues_mks(start_year, end_year):
    for year in range(start_year, end_year + 1):
        with requests.get("https://pubsonline.informs.org/loi/mksc/group/d" + str(year//10 * 10) + ".y" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for link in soup.findAll("a", "issue-info__vol-issue"):
                issue_pubsonline("https://pubsonline.informs.org" + link.get("href"), str(year), "MKS")
    logging.info("Finished issues in MKS")

def issue_sd(s, journal):
    year = soup.find("h3", "js-issue-status text-s").text[-5:-1]
    for link in s.findAll("li", "js-article-list-item article-item u-padding-xs-top u-margin-l-bottom"):
        authors = link.find("div", "text-s u-clr-grey8 js-article__item__authors")
        if authors is None:
            continue
        else:
            authors = authors.text.split(", ")
        title = link.find("a", "anchor article-content-title u-margin-xs-top u-margin-s-bottom").text.replace(" ", "_")
        download_name = rename(authors, journal, year, title)
        doi = link.find("div", text=lambda text: text and "doi.org" in text).text.split("doi.org/")[1]
        download_pdf(doi, download_name)

def issues_sd(url, journal):
    prev_issue = True
    while(prev_issue):
        with requests.get(url, headers=headers) as html:
            soup = BeautifulSoup(html.text)
            issue_sd(soup, journal)
            url = soup.find("a", "anchor text-m u-padding-s-ver u-display-block")
            prev_issue = url.get("aria-disabled") == "false"
            if (prev_issue):
                url = "https://www.sciencedirect.com" + url.get("href") 
logging.basicConfig(format='%(levelname)8s: %(message)s')
logging.getLogger().setLevel(logging.INFO)

def issues_jcr(start, end):
    for year in range(start, end + 1):
        with requests.get("https://academic.oup.com/jcr/issue-archive/" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("div", "customLink"):
                issue_jcr(issue.find("a").get("href"))
    logging.info("Finished issues in JCR")
    
def issues_jcp_w(start, end):
    for year in range(start, end + 1):
        with requests.get("https://onlinelibrary.wiley.com/loi/15327663/year/" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("a", "visitable"):
                issue_wiley(issue.get("href"), "JCP")
    logging.info("Finished issues in JCP (wiley)")
    
def issues_pm(start, end):
    for year in range(start, end + 1):
        with requests.get("https://onlinelibrary.wiley.com/loi/15206793/year/" + str(year), headers=headers) as html:
            soup = BeautifulSoup(html.text)
            for issue in soup.findAll("a", "visitable"):
                issue_wiley(issue.get("href"), "PM")
    logging.info("Finished issues in PM")
# site_str = input("Chose the site you want to download the issues from:\n")

# in_str = input("Enter the volumes want to download the issues (1-27): ")
# temp = re.findall(r'\d+', in_str)
# in_str = input("Enter the year want to download the issues (1990-2020): ")


issues_jcr(1974, 2020)
issues_jcp_w(1992, 2020)
issues_pm(1984, 2020)
issues_jm(1934, 2020)
issues_jppm(1982, 2020)
issues_jmr(1964, 2020)
issues_mks(1982, 2020)
issues_mgs(1954, 2020)
issues_jams(1, 48)
issues_sd("https://www.sciencedirect.com/journal/journal-of-consumer-psychology/latest", "JCP")
issues_sd("https://www.sciencedirect.com/journal/journal-of-business-research/latest", "JBR")
issues_sd("https://www.sciencedirect.com/journal/appetite/latest", "Appetite")



logging.info("Congrats! All the articles are downloaded! ")

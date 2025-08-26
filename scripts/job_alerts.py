import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import re
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure retry mechanism
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# Job boards
JOB_SITES = [
    "https://us.trabajo.org/jobs?q=graphic+designer",
    "https://gb.trabajo.org/jobs?q=graphic+designer",
    "https://ke.trabajo.org/jobs?q=graphic+designer",
    "https://remote.co/remote-jobs/search/?search_keywords=graphic+designer",
    "https://www.myjobmag.co.ke/search/jobs?q=graphic+designer",
    "https://www.brightermonday.co.ke/jobs?q=graphic+designer",
    "https://www.fuzu.com/kenya/jobs?search=graphic+designer",
    "https://www.summitrecruitment-search.com/job-search/?search=graphic+designer",
    "https://shortlist.net/jobs/?search=graphic+designer",
    "https://www.myjobsinkenya.com/search?q=graphic+designer",
    "https://www.jobsinkenya.co.ke/search?q=graphic+designer",
    "https://opportunitiesforyoungkenyans.co.ke",
    "https://www.jobwebkenya.com",
    "https://www.kenyajob.com/job-vacancies-kenya",
    "https://cdl.co.ke/jobs",
    # Replaced invalid URL; update with correct one after testing
    "https://ngojobsinafrica.com",
    "https://www.indeed.com/q-graphic-designer-jobs.html",
    "https://www.glassdoor.com/Job/kenya-graphic-designer-jobs-SRCH_IL.0,5_IN110_KO6,23.htm",
    "https://www.unjobnet.org/jobs?keywords=graphic+design&location=",
    "https://remoteok.com/remote-graphic+design-jobs",
    "https://careers.google.com/jobs/results/?q=graphic%20design",
    "https://www.linkedin.com/jobs/search/?keywords=graphic%20designer"
]

# Email regex
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def scrape_company_leads():
    leads = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    for site in JOB_SITES:
        try:
            logging.info(f"Scraping {site}")
            r = session.get(site, headers=headers, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            # Site-specific parsing
            companies = []
            if "indeed.com" in site:
                companies = [c.get_text(strip=True) for c in soup.find_all("span", class_="companyName")]
            elif "linkedin.com" in site:
                companies = [c.get_text(strip=True) for c in soup.find_all("a", class_="job-card-container__company-name")]
            else:
                companies = [c.get_text(strip=True) for c in soup.find_all(["h3", "h4", "span", "p"]) if "company" in c.get_text(strip=True).lower()]

            companies = list(set(companies))[:5]
            emails = re.findall(EMAIL_REGEX, r.text)
            emails = list(set(emails))[:5]

            if companies or emails:
                leads.append({
                    "site": site,
                    "companies": companies,
                    "emails": emails
                })
                logging.info(f"Found {len(companies)} companies and {len(emails)} emails at {site}")

        except RequestException as e:
            logging.error(f"Error scraping {site}: {e}")
        time.sleep(2)  # Delay to avoid rate-limiting

    return leads

def send_email(leads):
    sender = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASS")
    receiver = os.environ.get("EMAIL_RECEIVER")

    if not all([sender, password, receiver]):
        logging.error("Missing one or more email environment variables: EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER")
        raise ValueError("Email configuration incomplete")

    msg = MIMEMultipart("alternative")
    date_str = datetime.now().strftime("%Y-%m-%d")
    msg["Subject"] = f"Company Leads - {date_str}"
    msg["From"] = sender
    msg["To"] = receiver

    html_content = "<h2>Potential Companies & Contacts</h2>"
    for lead in leads:
        html_content += f"<h3>Source: {lead['site']}</h3>"
        if lead["companies"]:
            html_content += "<p><b>Companies:</b><br>" + "<br>".join(lead["companies"]) + "</p>"
        if lead["emails"]:
            html_content += "<p><b>Emails:</b><br>" + "<br>".join(lead["emails"]) + "</p>"
        html_content += "<hr>"

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        logging.info("✅ Leads email sent successfully")
    except Exception as e:
        logging.error(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    logging.info("Starting job alerts script")
    leads = scrape_company_leads()
    if leads:
        send_email(leads)
    else:
        logging.warning("No leads found today")

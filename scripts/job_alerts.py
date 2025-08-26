import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ===============================
# CONFIGURATION
# ===============================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"
EMAIL_RECEIVER = "your_email@gmail.com"

# List of job sites
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
    "https://www.ngojobvacancy.com",
    "https://www.indeed.com/q-graphic-designer-jobs.html",
    "https://www.glassdoor.com/Job/kenya-graphic-designer-jobs-SRCH_IL.0,5_IN110_KO6,23.htm",
    "https://www.unjobnet.org/jobs?keywords=graphic+design&location=",
    "https://remoteok.com/remote-graphic+design-jobs",
]

# ===============================
# SCRAPER FUNCTION
# ===============================
def scrape_jobs(url):
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        
        jobs = []
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            if "graphic" in text.lower() or "design" in text.lower():
                jobs.append(f"{text} - {link['href']}")
        return jobs
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# ===============================
# EMAIL SENDER
# ===============================
def send_email(job_list):
    msg = MIMEMultipart("alternative")
    date_str = datetime.now().strftime("%Y-%m-%d")
    msg["Subject"] = f"Daily Job Alerts - {date_str}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECEIVER

    if not job_list:
        body = "No new jobs found today."
    else:
        body = "<h2>Daily Job Alerts</h2><ul>"
        for job in job_list:
            body += f"<li>{job}</li>"
        body += "</ul>"

    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    all_jobs = []
    for site in JOB_SITES:
        print(f"Scraping: {site}")
        jobs = scrape_jobs(site)
        all_jobs.extend(jobs)

    send_email(all_jobs)
    print("✅ Job alert email sent successfully!")

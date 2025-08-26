import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import re

# ----------------------------
# Job boards (same as job_alerts.py)
# ----------------------------
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
    "https://remote.co/remote-jobs/design",
    "https://remoteok.com/remote-graphic+design-jobs",
    "https://careers.google.com/jobs/results/?q=graphic%20design",
    "https://www.google.com/search?q=graphic+design+jobs+in+kenya",
    "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4265979516&distance=25&f_TPR=a1752603444-&geoId=100710459&keywords=graphic%20designer",
    "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4267362938&distance=25&f_TPR=a1752612990-&geoId=103644278&",
    "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4265979516&distance=25&f_TPR=a1752584014-&f_WT=2%2C3&geoId=101165590&keywords=graphic%20designer"
]

# ----------------------------
# Email regex for scraping
# ----------------------------
EMAIL_REGEX = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"

def scrape_company_leads():
    leads = []
    for site in JOB_SITES:
        try:
            r = requests.get(site, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(r.text, "html.parser")

            # Try to extract company names
            companies = [c.get_text(strip=True) for c in soup.find_all(["h3", "h4", "span", "p"]) if "company" in c.get_text(strip=True).lower()]
            companies = list(set(companies))

            # Extract emails from page
            emails = re.findall(EMAIL_REGEX, r.text)
            emails = list(set(emails))

            if companies or emails:
                leads.append({
                    "site": site,
                    "companies": companies[:5],  # limit for sanity
                    "emails": emails[:5]
                })

        except Exception as e:
            print(f"Error scraping {site}: {e}")

    return leads

def send_email(leads):
    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = os.environ["EMAIL_RECEIVER"]

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
        print("✅ Leads email sent successfully.")
    except Exception as e:
        print(f"❌ Error sending email: {e}")

if __name__ == "__main__":
    leads = scrape_company_leads()
    if leads:
        send_email(leads)
    else:
        print("No leads found today.")

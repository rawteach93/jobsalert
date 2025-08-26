
import os, re, json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG = json.load(open(os.path.join(BASE, 'config.json')))
KEYWORDS = [k.lower() for k in CONFIG.get('keywords', [])]

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

def match_keywords(text):
    text = (text or '').lower()
    return any(k in text for k in KEYWORDS)

def extract_jobs_from_url(url):
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
    except Exception as e:
        print('ERROR fetching', url, e)
        return []
    soup = BeautifulSoup(resp.text, 'lxml')
    results = []
    # look for anchors that look like job links
    for a in soup.find_all('a', href=True):
        txt = a.get_text(" ", strip=True)
        href = a['href']
        if match_keywords(txt) or match_keywords(href):
            link = href if href.startswith('http') else requests.compat.urljoin(url, href)
            results.append({'title': txt, 'company':'', 'link': link, 'snippet': txt})
    # dedupe
    uniq = {r['link']: r for r in results if r.get('link')}
    return list(uniq.values())

def fetch_job_details(job):
    try:
        resp = requests.get(job['link'], timeout=12, headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(resp.text, 'lxml')
        title = job['title'] or (soup.find('h1') and soup.find('h1').get_text(strip=True)) or ''
        company = ''
        # try common company selectors
        comp = soup.find(lambda t: t.name in ['div','span'] and 'company' in ' '.join(t.get('class',[]))) or soup.find('meta', {'property':'og:site_name'})
        if comp:
            company = comp.get('content') if comp.get('content') else comp.get_text(strip=True)
        snippet = job.get('snippet') or soup.get_text(" ", strip=True)[:400]
        date = ''
        return {'title': title, 'company': company, 'link': job['link'], 'snippet': snippet, 'date': date}
    except Exception as e:
        return job

def build_job_list(urls):
    jobs = []
    for url in urls:
        found = extract_jobs_from_url(url)
        for f in found:
            details = fetch_job_details(f)
            jobs.append(details)
    return jobs

def load_existing_csv(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path, dtype=str).to_dict('records')
        except:
            return []
    return []

def save_csv(path, rows):
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)

def send_email(subject, html_body, plain_body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    if not (GMAIL_USER and GMAIL_APP_PASSWORD and RECIPIENT_EMAIL):
        print('Missing email environment variables.')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = RECIPIENT_EMAIL

    part1 = MIMEText(plain_body, 'plain')
    part2 = MIMEText(html_body, 'html')

    msg.attach(part1)
    msg.attach(part2)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    server.quit()
    return True

def main():
    urls = CONFIG.get('sources', [])
    jobs = build_job_list(urls)

    # filter
    filtered = []
    for j in jobs:
        text = ' '.join([j.get('title',''), j.get('snippet','')]).lower()
        if any(k in text for k in KEYWORDS):
            jid = re.sub(r'\\W+', '_', j.get('link','')[:80])
            filtered.append({'id': jid, 'title': j.get('title',''), 'company': j.get('company',''), 'link': j.get('link',''), 'snippet': j.get('snippet','')})

    csv_path = os.path.join(DATA_DIR, 'job_alerts.csv')
    existing = load_existing_csv(csv_path)
    existing_ids = set([e.get('id') for e in existing]) if existing else set()

    new_jobs = [j for j in filtered if j['id'] not in existing_ids]

    combined = (existing or []) + new_jobs
    if combined:
        save_csv(csv_path, combined)

    # prepare email
    date_str = datetime.utcnow().strftime('%d %b %Y')
    subject = f\"Daily Job Alerts - {date_str}\"
    if not new_jobs:
        plain = \"No new graphic design or branding jobs found today.\"
        html = \"<p>No new graphic design or branding jobs found today.</p>\"
    else:
        html_lines = ['<h2>Graphic Design & Branding Jobs</h2>', '<ol>']
        plain_lines = []
        for j in new_jobs:
            plain_lines.append(f\"{j['title']} — {j['company']}\\n{j['link']}\\n\")
            html_lines.append(f\"<li><strong>{j['title']}</strong> — {j['company']}<br><a href=\\\"{j['link']}\\\">Apply / Details</a><p>{j['snippet']}</p></li>\")
        html_lines.append('</ol>')
        plain = '\\n'.join(plain_lines)
        html = ''.join(html_lines)

    send_email(subject, html, plain)
    print('Job alerts email sent.')

if __name__ == '__main__':
    main()

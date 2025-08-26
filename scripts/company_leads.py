
import os, re, json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

BASE = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG = json.load(open(os.path.join(BASE, 'config.json')))

GMAIL_USER = os.environ.get('GMAIL_USER')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')

def extract_emails(text):
    if not text:
        return []
    emails = re.findall(r'[\\w\\.-]+@[\\w\\.-]+', text)
    return list(set(emails))

def scan_for_company_contacts(urls):
    leads = []
    for url in urls:
        try:
            resp = requests.get(url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
        except Exception as e:
            print('ERROR fetching', url, e)
            continue
        soup = BeautifulSoup(resp.text, 'lxml')
        text = soup.get_text(" ", strip=True)
        emails = extract_emails(text)
        company = ''
        og = soup.find('meta', property='og:site_name') or soup.find('meta', attrs={'name':'og:site_name'})
        if og and og.get('content'):
            company = og.get('content')
        else:
            title = soup.find('title')
            company = title.get_text(strip=True) if title else url
        for e in emails:
            leads.append({'company': company, 'email': e, 'source': url, 'found_at': datetime.utcnow().isoformat()})
    return leads

def load_existing(path):
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
    leads = scan_for_company_contacts(urls)
    csv_path = os.path.join(DATA_DIR, 'company_leads.csv')
    existing = load_existing(csv_path)
    existing_emails = set([e.get('email') for e in existing]) if existing else set()

    new_leads = [l for l in leads if l['email'] not in existing_emails]
    combined = (existing or []) + new_leads
    if combined:
        save_csv(csv_path, combined)

    date_str = datetime.utcnow().strftime('%d %b %Y')
    subject = f\"Hiring Companies - {date_str}\"
    if not new_leads:
        plain = \"No new company contacts (emails) found today.\"
        html = \"<p>No new company contacts (emails) found today.</p>\"
    else:
        html_lines = ['<h2>New Company Contacts</h2>', '<ol>']
        plain_lines = []
        for l in new_leads:
            plain_lines.append(f\"{l['company']} — {l['email']} — {l['source']}\")
            html_lines.append(f\"<li><strong>{l['company']}</strong> — {l['email']} <br><em>Source:</em> <a href=\\\"{l['source']}\\\">{l['source']}</a></li>\")
        html_lines.append('</ol>')
        plain = '\\n'.join(plain_lines)
        html = ''.join(html_lines)

    send_email(subject, html, plain)
    print('Company leads email sent.')

if __name__ == '__main__':
    main()

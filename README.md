
# Job Alerts & Company Leads Automation (Ready for GitHub)

This repository contains two GitHub Actions that run daily and:
1. Scrape job boards for **Graphic Design & Branding** jobs and send a daily email with new listings.
2. Scan the same sources for **company contact emails** and send a daily email with new leads.

## Files
- `.github/workflows/job_alerts.yml` - workflow for job alerts (runs daily)
- `.github/workflows/company_leads.yml` - workflow for leads (runs daily)
- `scripts/job_alerts.py` - scraper + HTML email sender for job alerts
- `scripts/company_leads.py` - scanner + HTML email sender for company leads
- `config.json` - list of sources and keywords
- `requirements.txt` - Python dependencies
- `data/` - runtime CSV backups (created by the workflows)

## Setup
1. Create a new GitHub repository and upload the files from this repo (or use the zip upload).
2. In your GitHub repository settings -> Secrets -> Actions, add the following secrets:
   - `GMAIL_USER` : your Gmail address (e.g., yourname@gmail.com)
   - `GMAIL_APP_PASSWORD` : a Gmail App Password (see note below)
   - `RECIPIENT_EMAIL` : where to send the daily emails (can be same as GMAIL_USER)

### Creating a Gmail App Password
1. Ensure your account has 2-Step Verification enabled.
2. Go to Google Account -> Security -> App passwords.
3. Choose "Mail" and "Other" or "Custom name" and create a password. Copy it.
4. Paste the generated password into the `GMAIL_APP_PASSWORD` secret in GitHub.

## Notes & Next steps
- The scraping logic uses conservative HTML parsing and tries to work across many sites, but some sites (e.g., LinkedIn search results) are dynamic and may require additional custom parsing or an API. You asked to keep LinkedIn off heavy scraping; the scripts will attempt to use the LinkedIn links you provided with simple requests where possible.
- If you want more robust parsing for specific sites, I can customize selectors per site in `scripts/`.
- CSV backups are saved in `/data` and committed back to the repository by the workflow so you can download a running archive of leads & jobs.

## License
MIT

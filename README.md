# Freight Indices Newsletter

Automated weekly newsletter system for tracking container freight indices (WCI, SCFI, IACI) with data collection, visualization, self-service subscription and email distribution.

**Signup page:** https://doiennoson.github.io/freight-indices-newsletter/

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#️-system-architecture)
- [Setup Instructions](#-setup-instructions)
- [Configuration](#️-configuration)
- [Subscriber Management](#-subscriber-management)
- [Data Sources](#-data-sources)
- [Automation Schedule](#-automation-schedule)
- [File Structure](#-file-structure)
- [Troubleshooting](#-troubleshooting)
- [Maintenance](#-maintenance)
- [Changelog](#-changelog)

---

## 🎯 Overview

This project automatically:
1. **Scrapes** freight index data from emails (WCI, IACI) and an API (SCFI)
2. **Stores** historical data in CSV files
3. **Generates** visual charts showing trends
4. **Sends** a weekly newsletter to confirmed subscribers
5. **Manages** signups, confirmations (double opt-in) and unsubscribes

**Target Audience:** Logistics professionals, freight forwarders, supply chain analysts

---

## ✨ Features

### Data Collection
- ✅ **WCI (World Container Index)** - Scraped from Drewry emails
- ✅ **IACI (Intra-Asia Container Index)** - Scraped from Drewry emails
- ✅ **SCFI (Shanghai Containerized Freight Index)** - Fetched from Shanghai Shipping Exchange API

### Visualization
- 📊 **WCI vs SCFI Chart** - Comparative analysis since January 2025
- 📊 **IACI Chart** - Full historical data with complete timeline
- 🎨 Color-coded lines: WCI (dark blue #0E2841), SCFI (light green #AAD228)

### Newsletter
- 📧 **HTML Email** with embedded charts
- 📈 **Performance Table** with current values, weekly changes, and year-over-year comparison
- 🔔 **Automatic Alerts** when data collection fails
- 🚪 **Unsubscribe link** in every email plus `List-Unsubscribe` header (Gmail shows its own unsubscribe button)

### Subscriptions
- 📝 **Signup page** on GitHub Pages with privacy notice and a weekly updated WCI chart
- 🔐 **Private subscriber list** in a Google Sheet, never in this public repository
- ✉️ **Double opt-in** by replying to a confirmation email
- 🧹 **Automatic cleanup** of unconfirmed and old unsubscribed entries

### Signal Definitions
- **▲ Green Triangle:** Weekly change > +1.0%
- **▼ Red Triangle:** Weekly change < -1.0%
- **● Blue Circle:** Weekly change between -1.0% and +1.0% (stable)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  cron-job.org: Fri 15:47 Beijing time                   │
│        │  POST /repos/.../dispatches (weekly-newsletter)│
├────────┼────────────────────────────────────────────────┤
│        ▼          GITHUB ACTIONS                        │
│  Scraper                                                │
│   ├─ WCI Email (Drewry)                                 │
│   ├─ IACI Email (Drewry)                                │
│   └─ SCFI API (SSE)          → CSV files committed      │
│        │ on success (workflow_run)                      │
│        ▼                                                │
│  Plot Generator              → PNG charts committed     │
│        │ on success (workflow_run)                      │
│        ▼                                                │
│  Newsletter                                             │
│   ├─ Process signups/unsubscribes (Google Sheet)        │
│   ├─ Generate HTML                                      │
│   └─ Send to confirmed subscribers                      │
│                                                         │
│  Manage Subscribers (every 6 hours)                     │
│   └─ Confirmation emails, replies, unsubscribes         │
└─────────────────────────────────────────────────────────┘

Signup: GitHub Pages (docs/) → Google Form → private Google Sheet
```

---

## 🚀 Setup Instructions

### Prerequisites
- GitHub account
- Gmail account with App Password enabled (receives Drewry emails, sends the newsletter)
- Google account for Google Forms / Sheets and a Google Cloud project
- Free account at [cron-job.org](https://cron-job.org)

### Step 1: Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select **Read and write permissions**
3. Click **Save**

### Step 2: Gmail Secret

1. Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. **Name:** `EMAIL_CONFIG`, **Value:** `your-email@gmail.com:your-app-password:smtp.gmail.com:587`

How to get a Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable **2-Factor Authentication**
3. Go to **App passwords**, create one for "Mail"
4. Use the 16-character password (not your regular Gmail password) in `EMAIL_CONFIG`

### Step 3: Signup Form and Subscriber Sheet

1. Create a Google Form with **Settings → Responses → Collect email addresses: Responder input** (not "Verified", which would force a Google login) and **Limit to 1 response** off
2. Add one required checkbox question **Consent** with the consent text
3. Add the privacy notice link to the form description
4. **Responses → Link to Sheets → Create a new spreadsheet**
5. Sharing of the sheet must stay **Restricted** (never "Anyone with the link")
6. Put the sheet ID into `SHEET_ID` in `src/subscriber_manager.py` and the form URL into `docs/index.html`

### Step 4: Google Service Account

1. In the [Google Cloud Console](https://console.cloud.google.com), enable the **Google Sheets API**
2. **IAM & Admin → Service Accounts → Create service account** (no role needed)
3. **Actions → Manage keys → Add key → Create new key → JSON**
4. Share the sheet with the service account address as **Editor** (without notification)
5. Add the complete JSON file content as repository secret `GOOGLE_SERVICE_ACCOUNT`, then delete the local file

### Step 5: GitHub Pages

**Settings → Pages → Build and deployment → Source: Deploy from a branch**, branch `main`, folder `/docs`.

### Step 6: cron-job.org Trigger

1. Create a **fine-grained personal access token** on GitHub (**Settings → Developer settings → Personal access tokens → Fine-grained tokens**): only this repository, permission **Contents: Read and write**
2. Create a cronjob on cron-job.org:
   - **URL:** `https://api.github.com/repos/DoiEnnoson/freight-indices-newsletter/dispatches`
   - **Schedule:** Custom, Friday, 15:47, time zone `Asia/Shanghai`
   - **Method:** `POST`
   - **Headers:** `Accept: application/vnd.github+json`, `Authorization: Bearer <token>`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
   - **Body:** `{"event_type":"weekly-newsletter"}`
3. **Test run** must return HTTP **204** and start the whole chain (scraper, charts, newsletter)

---

## ⚙️ Configuration

### Secrets

| Secret | Required | Content |
|--------|----------|---------|
| `EMAIL_CONFIG` | yes | `email:app-password:smtp_server:port` of the Gmail account |
| `GOOGLE_SERVICE_ACCOUNT` | yes | JSON key of the service account with editor access to the subscriber sheet |
| `ALERT_EMAIL` | no | Recipient of scraper warnings; defaults to the `EMAIL_CONFIG` address |

### Email Configuration

The `EMAIL_CONFIG` secret uses this format:

```
email:password:smtp_server:smtp_port
```

- **email:** Gmail address
- **password:** Gmail App Password (16 characters, no spaces)
- **smtp_server:** `smtp.gmail.com`
- **smtp_port:** `587` (STARTTLS)

The IMAP server is derived from the SMTP server (`smtp` → `imap`).

### Chart Customization

Edit `src/plot_generator.py`:

```python
COLOR_WCI = "#0E2841"   # Dark blue
COLOR_SCFI = "#AAD228"  # Light green
COLOR_IACI = "#0E2841"  # Dark blue
fig, ax = plt.subplots(figsize=(14, 8))  # Width x Height in inches
start_date = pd.Timestamp('2025-01-01')  # WCI/SCFI start date
```

### Newsletter Template

Edit `html_template.html` to customize the newsletter design. Placeholders `{{DATE}}` and `{{TABLE_ROWS}}` are filled by `newsletter_generator.py`; charts are embedded via `cid:chart_wci_scfi` and `cid:chart_iaci`.

---

## 👥 Subscriber Management

Subscribers are stored in a **private Google Sheet**, never in this public repository. Actions logs are public and therefore never contain subscriber addresses; the scripts only log counts.

### Flow (double opt-in)

1. The signup page (`docs/index.html`) links to the Google Form (email + consent)
2. The form writes into the sheet (`Timestamp`, `Email Address`, `Consent`)
3. `src/subscriber_manager.py` runs every 6 hours and before every newsletter:
   - sends a confirmation email with a token `[FIN-xxxxxxxx]` in the subject to each new entry
   - confirms an entry when a reply containing its token arrives in the Gmail inbox
   - unsubscribes the sender of any email with `Unsubscribe` in the subject (only entries created before that email, so a later re-signup is not affected)
   - marks repeated signups of an active address as duplicate and removes them
   - deletes unconfirmed entries after 30 days and unsubscribed entries after 3 years
4. The newsletter is sent only to entries with status `confirmed`

### Sheet Columns

| Column | Written by | Meaning |
|--------|-----------|---------|
| `Timestamp`, `Email Address`, `Consent` | Google Form | Signup data |
| `Status` | script | `pending`, `confirmed`, `unsubscribed` |
| `Token` | script | Code in the confirmation email subject |
| `ConfirmationSentUTC` | script | Time the confirmation email was sent |
| `ConfirmedUTC` | script | Time of the confirming reply |
| `UnsubscribedUTC` | script | Time of the unsubscribe email |

The script adds its columns automatically. **Do not rename any column.** The script only writes its own columns and never touches the form columns.

### Manual Changes

- **Stop sending to someone:** set `Status` to `unsubscribed`
- **Erase someone's data (GDPR request):** delete the row
- **Export:** File → Download → CSV

---

## 📊 Data Sources

### WCI (World Container Index)
- **Source:** Drewry emails in the configured Gmail inbox
- **Sender:** `noreply@drewry.co.uk`
- **Subject contains:** "World Container Freight Market Update"
- **Update Frequency:** Weekly (Thursday)
- **Extraction:** "(WCI) … $X,XXX per 40ft container"

### IACI (Intra-Asia Container Index)
- **Source:** Same Drewry email as the WCI
- **Extraction:** "(IACI) … $X,XXX per 40ft container"

### SCFI (Shanghai Containerized Freight Index)
- **Source:** Shanghai Shipping Exchange JSON API
- **Endpoint:** `https://en.sse.net.cn/currentIndex?indexName=scfi`
- **Update Frequency:** Weekly, Fridays around 15:00 Beijing time; shifted around Chinese public holidays
- **Fields used:** `data.currentDate` (publication date) and `data.lineDataList[0].currentContent` (composite index, `lineName_EN: "Comprehensive Index"`)
- **Note:** The API provides no publication time, neither in the payload nor in HTTP headers (`Last-Modified` is absent), only the date

---

## ⏰ Automation Schedule

Only the scraper has a fixed schedule. It is triggered externally by cron-job.org via the GitHub API (`repository_dispatch`, event type `weekly-newsletter`), because GitHub's own scheduler regularly delayed runs by 4 to 10 hours. Charts and newsletter are chained via `workflow_run`, so they always run on fresh data and stop if a previous step fails.

| Trigger | Workflow | Action |
|---------|----------|--------|
| **Fri 15:47 Beijing time** via cron-job.org (07:47 UTC, 08:47 CET / 09:47 CEST) | Weekly Freight Indices Scraper | Fetch WCI, IACI, SCFI data |
| after successful cron-job.org scraper run | Generate Freight Indices Plots | Create charts from CSV data |
| after successful chained plot run | Send Weekly Newsletter | Process signups, send emails |
| **every 6 hours** at :17 (GitHub schedule) | Manage Subscribers | Confirmations and unsubscribes |

China has no daylight saving time; the cron-job.org job runs in time zone `Asia/Shanghai`, so the trigger time never shifts.

**Manual Trigger:** All workflows can be started via **Actions** → **Workflow name** → **Run workflow**. A manual scraper run does **not** trigger charts and newsletter; a manual newsletter run sends immediately to all confirmed subscribers.

---

## 📁 File Structure

```
freight-indices-newsletter/
├── .github/
│   └── workflows/
│       ├── weekly_scraper.yml          # Scraper, triggered by cron-job.org
│       ├── generate_plots.yml          # Charts, chained after the scraper
│       ├── send_newsletter.yml         # Newsletter, chained after the charts
│       └── manage_subscribers.yml      # Signup processing every 6 hours
│
├── src/
│   ├── scraper.py                      # Data collection
│   ├── plot_generator.py               # Chart generation
│   ├── newsletter_generator.py         # Email generation and sending
│   └── subscriber_manager.py           # Double opt-in, unsubscribes, sheet access
│
├── docs/                               # GitHub Pages
│   ├── index.html                      # Signup page
│   ├── privacy.html                    # Privacy notice (GDPR)
│   ├── wci_chart.png                   # WCI chart (last 12 months), updated weekly
│   └── style.css
│
├── data/
│   ├── wci.csv                         # WCI historical data
│   ├── scfi.csv                        # SCFI historical data
│   └── iaci.csv                        # IACI historical data
│
├── output/
│   ├── wci_scfi/wci_scfi_chart.png     # Combined WCI/SCFI chart
│   └── iaci/iaci_chart.png             # IACI chart
│
├── html_template.html                  # Newsletter HTML template
├── requirements.txt                    # Python dependencies
└── README.md                           # This file
```

---

## 🐛 Troubleshooting

### Scraper Issues

#### "No WCI/IACI emails found in last 14 days"
1. Check whether Drewry emails arrive in the Gmail inbox (also check spam)
2. Verify the sender is exactly `noreply@drewry.co.uk`
3. Ensure `EMAIL_CONFIG` has correct credentials

#### "SCFI API request failed"
1. Check whether the API responds: https://en.sse.net.cn/currentIndex?indexName=scfi
2. Check whether the response format has changed
3. Review the scraper logs

#### "Connection unexpectedly closed" (SMTP)
1. Verify `EMAIL_CONFIG` format: `email:app-password:smtp.gmail.com:587`
2. Ensure a Gmail **App Password** is used and 2FA is enabled

### Trigger Issues

#### Newsletter did not arrive on Friday
1. **Actions** tab: did "Weekly Freight Indices Scraper" run with event `repository_dispatch`?
2. If not, check the cron-job.org execution history:
   - **401:** token expired or revoked → create a new token and update the `Authorization` header
   - **404:** token lacks access to this repository or **Contents: Read and write**
3. If the scraper failed, charts and newsletter are skipped on purpose; fix the cause and start "Send Weekly Newsletter" manually

### Chart Generation Issues

#### "No data available from 2025-01-01"
1. Check that the CSV files contain dates >= 2025-01-01 in DD.MM.YYYY format
2. Ensure at least 2 data points exist per CSV

### Subscriber Issues

#### "No confirmed subscribers, nothing to send"
1. Check that at least one row in the sheet has `Status` = `confirmed`

#### Sheet access errors
1. Verify the sheet is shared with the service account as **Editor**
2. Verify `GOOGLE_SERVICE_ACCOUNT` contains the complete JSON key
3. Verify the Google Sheets API is enabled in the Google Cloud project

#### Reply sent, but status stays `pending`
1. Confirmations are processed by the next run (every 6 hours at 00:17, 06:17, 12:17, 18:17 UTC) or the next newsletter run
2. The reply must keep the subject with `[FIN-xxxxxxxx]` and arrive in the inbox of the `EMAIL_CONFIG` account

### Warning Emails

A warning email goes to `ALERT_EMAIL` (default: the `EMAIL_CONFIG` address, currently `doisnews@gmail.com`) when:
- ❌ the WCI or IACI email was not found in the last 14 days
- ❌ the SCFI API returned no data
- ❌ an email was found but value/date extraction failed

---

## 🔧 Maintenance

### Adding Historical Data
1. Edit the CSV files in `data/` (format `Date,Value`, dates as DD.MM.YYYY)
2. Commit and push; charts reflect the data on the next run

### Changing the Newsletter Schedule
Change the execution time of the cronjob on cron-job.org. No change in the repository is needed.

### Renewing the cron-job.org Token
Fine-grained tokens expire. Before expiry, create a new token (see [Step 6](#step-6-cron-joborg-trigger)) and replace it in the `Authorization` header of the cronjob.

### Dependencies

All Python dependencies are listed in `requirements.txt` and installed automatically in each workflow run:

```txt
beautifulsoup4==4.12.3
pandas==2.2.0
requests==2.31.0
matplotlib==3.8.2
lxml==5.1.0
gspread==6.1.2
google-auth==2.35.0
```

---

## 🛡️ Security and Privacy

This repository is **public**. Therefore:

1. ✅ **No personal data in the repository** - subscribers live in the private Google Sheet
2. ✅ **No addresses in logs** - Actions logs are public; scripts log counts only
3. ✅ **Credentials only as GitHub Secrets** - Gmail App Password, service account key
4. ✅ **Sheet sharing restricted** - only the owner and the service account have access
5. ✅ **Minimal token scope** - the cron-job.org token can only access this repository's contents
6. ✅ **GDPR** - consent via form, double opt-in, unsubscribe in every email, privacy notice, automatic deletion periods

Note: Git history before October 2026 still contains the former `subscribers.csv` and a maintainer address in `scraper.py`.

---

## 📝 Changelog

### 2.0.0 (October 2026)

**Subscription management**
- Signup page and privacy notice on GitHub Pages (`docs/`), linking to a Google Form
- Subscriber list moved from `subscribers.csv` (deleted, would have been public) to a private Google Sheet, accessed via a Google service account
- Double opt-in: confirmation email with token, confirmation by reply (`src/subscriber_manager.py`, workflow `manage_subscribers.yml` every 6 hours)
- Unsubscribe via link (`mailto:` with subject `Unsubscribe`) and `List-Unsubscribe` header in every newsletter
- Automatic deletion of unconfirmed (30 days) and unsubscribed (3 years) entries
- Subscriber addresses removed from all logs

**Scheduling**
- Previous setup: three independent GitHub cron jobs at fixed times (Fri 12:00 / 12:30 / 13:00 UTC). GitHub started them 4 to 10 hours late, and their order was not guaranteed, so a newsletter could have been sent with the previous week's charts
- New setup: only the scraper is triggered, externally by cron-job.org on Fridays 15:47 Beijing time (shortly after the SCFI publication at about 15:00); charts and newsletter follow via `workflow_run` and only after success
- Manual scraper runs no longer trigger a newsletter

**Other**
- Scraper warning recipient moved from the code to the optional secret `ALERT_EMAIL`
- All public texts (signup page, privacy notice, confirmation email) in English
- SCFI API analysed: it provides only the publication date, not the time; the composite index is identified by `lineName_EN: "Comprehensive Index"` / `dataItemTypeName: SCFI_T`

**Known open points**
- The SCFI scraper still takes the first entry of `lineDataList` instead of searching for `Comprehensive Index`, and falls back to today's date if the date cannot be parsed

### 1.1.0 (September 2026)
- WCI and IACI scrapers adapted to the restructured Drewry newsletter ("World Container Freight Market Update")

### 1.0.0 (February 2026)
- Initial release: scraper, charts, newsletter via GitHub Actions

---

## 📝 License & Disclaimer

### Data Sources
All data is sourced from publicly available information:
- **WCI & IACI:** Drewry emails (subscription-based but publicly sent)
- **SCFI:** Shanghai Shipping Exchange public API

No paid licenses or proprietary databases are violated.

### Disclaimer
This newsletter is for **informational purposes only**. Data may contain errors or delays. Not financial advice.

### Copyright
Newsletter Design © 2026 Dói Ennoson

---

## 📞 Support

- **Email:** doisnews@gmail.com
- **GitHub Issues:** https://github.com/DoiEnnoson/freight-indices-newsletter/issues

---

## 🎉 Acknowledgments

- **Drewry** - WCI and IACI data source
- **Shanghai Shipping Exchange** - SCFI data API
- **GitHub Actions** - Free CI/CD automation
- **cron-job.org** - Reliable external trigger
- **Matplotlib** - Chart generation library

---

**Last Updated:** October 2026
**Version:** 2.0.0

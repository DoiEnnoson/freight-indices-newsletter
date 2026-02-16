# Freight Indices Newsletter

Automated weekly newsletter system for tracking container freight indices (WCI, SCFI, IACI) with data collection, visualization, and email distribution.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Setup Instructions](#setup-instructions)
- [Configuration](#configuration)
- [Data Sources](#data-sources)
- [Automation Schedule](#automation-schedule)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

This project automatically:
1. **Scrapes** freight index data from emails (WCI, IACI) and APIs (SCFI)
2. **Stores** historical data in CSV files
3. **Generates** visual charts showing trends
4. **Sends** a weekly newsletter with analysis to subscribers

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
- 📝 **Subscriber Management** via CSV file

### Signal Definitions
- **▲ Green Triangle:** Weekly change > +1.0%
- **▼ Red Triangle:** Weekly change < -1.0%
- **● Blue Circle:** Weekly change between -1.0% and +1.0% (stable)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Friday 13:00 CET  →  Scraper                          │
│                       ├─ WCI Email (Drewry)            │
│                       ├─ IACI Email (Drewry)           │
│                       └─ SCFI API (SSE)                │
│                       ↓                                 │
│                    CSV Files Updated                    │
│                       ↓                                 │
│  Friday 14:30 CET  →  Plot Generator                   │
│                       ├─ WCI/SCFI Chart                │
│                       └─ IACI Chart                     │
│                       ↓                                 │
│                    PNG Files Created                    │
│                       ↓                                 │
│  Friday 15:00 CET  →  Newsletter Generator             │
│                       ├─ Load Subscriber List           │
│                       ├─ Generate HTML                  │
│                       └─ Send Emails                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup Instructions

### Prerequisites
- GitHub account
- Gmail account with App Password enabled
- Basic understanding of GitHub Actions

### Step 1: Fork/Clone Repository

```bash
git clone https://github.com/YOUR-USERNAME/freight-indices-newsletter.git
cd freight-indices-newsletter
```

### Step 2: Enable GitHub Actions

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

### Step 3: Configure Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following secret:

**Name:** `EMAIL_CONFIG`  
**Value:** `your-email@gmail.com:your-app-password:smtp.gmail.com:587`

#### How to Get Gmail App Password:
1. Go to https://myaccount.google.com/security
2. Enable **2-Factor Authentication** (if not already enabled)
3. Go to **App passwords** (under "Signing in to Google")
4. Create new app password for "Mail"
5. Copy the 16-character password
6. Use this password (not your regular Gmail password!) in `EMAIL_CONFIG`

### Step 4: Add Subscribers

Edit `subscribers.csv` in the repository root:

```csv
email
your-email@gmail.com
colleague@company.com
friend@example.com
```

### Step 5: Initialize Data Files

Create the following directory structure:

```
data/
├── wci.csv          (Date,Value format with DD.MM.YYYY)
├── scfi.csv         (Date,Value format with DD.MM.YYYY)
└── iaci.csv         (Date,Value format with DD.MM.YYYY)
```

**CSV Format Example:**
```csv
Date,Value
03.01.2025,1805.32
10.01.2025,1869.59
```

### Step 6: Test Run

1. Go to **Actions** tab
2. Select **Weekly Freight Indices Scraper**
3. Click **Run workflow** → **Run workflow**
4. Monitor the execution logs

---

## ⚙️ Configuration

### Email Configuration

The `EMAIL_CONFIG` secret uses this format:

```
email:password:smtp_server:smtp_port
```

**Example for Gmail:**
```
doisnews@gmail.com:abcd1234efgh5678:smtp.gmail.com:587
```

**Components:**
- **email:** Your Gmail address
- **password:** Gmail App Password (16 characters, no spaces)
- **smtp_server:** `smtp.gmail.com` for Gmail
- **smtp_port:** `587` for STARTTLS

### Subscriber Management

Edit `subscribers.csv` to add/remove recipients:

```csv
email
person1@example.com
person2@company.org
```

**Rules:**
- One email per line
- Duplicates are automatically removed
- Empty lines are ignored
- No additional columns needed

### Chart Customization

Edit `src/plot_generator.py` to customize:

**Colors:**
```python
COLOR_WCI = "#0E2841"   # Dark blue
COLOR_SCFI = "#AAD228"  # Light green
COLOR_IACI = "#0E2841"  # Dark blue
```

**Chart Size:**
```python
fig, ax = plt.subplots(figsize=(14, 8))  # Width x Height in inches
```

**Date Range (WCI/SCFI only):**
```python
start_date = pd.Timestamp('2025-01-01')  # Change start date
```

### Newsletter Template

Edit `html_template.html` to customize the newsletter design:
- Header styles (lines 26-54)
- Table formatting (lines 86-135)
- Footer content (lines 180-210)

---

## 📊 Data Sources

### WCI (World Container Index)
- **Source:** Drewry emails sent to configured Gmail account
- **Sender:** `noreply@drewry.co.uk`
- **Subject Contains:** "World Container Index"
- **Update Frequency:** Weekly (typically Thursday around 17:00 CET)
- **Format:** HTML email with value in text: "$X,XXX per 40ft container"

### IACI (Intra-Asia Container Index)
- **Source:** Drewry emails sent to configured Gmail account
- **Sender:** `noreply@drewry.co.uk`
- **Subject Contains:** "Intra-Asia"
- **Update Frequency:** Weekly (typically Friday by 13:00 CET)
- **Format:** HTML email with value in text: "$XXX per 40ft container"

### SCFI (Shanghai Containerized Freight Index)
- **Source:** Shanghai Shipping Exchange API
- **Endpoint:** `https://en.sse.net.cn/currentIndex?indexName=scfi`
- **Update Frequency:** Weekly (typically Friday morning)
- **Format:** JSON response with `currentContent` field

---

## ⏰ Automation Schedule

All times in **Central European Time (CET/CEST)**:

| Time | Workflow | Action | Duration |
|------|----------|--------|----------|
| **13:00** | Scraper | Fetch WCI, IACI, SCFI data | ~2 min |
| **14:30** | Plot Generator | Create charts from CSV data | ~1 min |
| **15:00** | Newsletter | Generate and send emails | ~2 min |

**Cron Schedule (GitHub Actions uses UTC):**

```yaml
# Scraper - 13:00 CET (11:00 UTC winter, 12:00 UTC summer)
- cron: '0 11 * * 5'

# Plot Generator - 14:30 CET (12:30 UTC winter, 13:30 UTC summer)
- cron: '30 12 * * 5'

# Newsletter - 15:00 CET (13:00 UTC winter, 14:00 UTC summer)
- cron: '0 13 * * 5'
```

**Manual Trigger:**
All workflows can be triggered manually via **Actions** → **Workflow name** → **Run workflow**

---

## 📁 File Structure

```
freight-indices-newsletter/
├── .github/
│   └── workflows/
│       ├── weekly_scraper.yml          # Scrapes data every Friday 13:00
│       ├── generate_plots.yml          # Creates charts every Friday 14:30
│       └── send_newsletter.yml         # Sends emails every Friday 15:00
│
├── src/
│   ├── scraper.py                      # Data collection logic
│   ├── plot_generator.py               # Chart generation
│   └── newsletter_generator.py         # Email generation and sending
│
├── data/
│   ├── wci.csv                         # WCI historical data
│   ├── scfi.csv                        # SCFI historical data
│   └── iaci.csv                        # IACI historical data
│
├── output/
│   ├── wci_scfi/
│   │   └── wci_scfi_chart.png         # Combined WCI/SCFI chart
│   └── iaci/
│       └── iaci_chart.png             # IACI chart
│
├── html_template.html                  # Newsletter HTML template
├── subscribers.csv                     # Email recipient list
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── newsletter.html                     # Generated newsletter (auto-created)
```

---

## 🐛 Troubleshooting

### Scraper Issues

#### Problem: "No WCI/IACI emails found in last 14 days"
**Solution:**
1. Check if Drewry emails are being received in the Gmail inbox
2. Verify the sender email is exactly `noreply@drewry.co.uk`
3. Check spam folder for Drewry emails
4. Ensure `EMAIL_CONFIG` secret has correct Gmail credentials

#### Problem: "SCFI API request failed"
**Solution:**
1. Check if API is accessible: https://en.sse.net.cn/currentIndex?indexName=scfi
2. Verify internet connectivity in GitHub Actions runner
3. Check API response format hasn't changed
4. Review scraper logs for specific error messages

#### Problem: "Connection unexpectedly closed" (SMTP)
**Solution:**
1. Verify `EMAIL_CONFIG` format: `email:app-password:smtp.gmail.com:587`
2. Ensure using Gmail **App Password**, not regular password
3. Check if 2FA is enabled on Gmail account
4. Verify port is `587` (not 465 or 25)

### Chart Generation Issues

#### Problem: "No data available from 2025-01-01"
**Solution:**
1. Check CSV files have data with dates >= 2025-01-01
2. Verify date format is DD.MM.YYYY in CSV files
3. Ensure at least 2 data points exist in each CSV

#### Problem: "Chart images not found"
**Solution:**
1. Verify plot generator workflow completed successfully
2. Check `output/wci_scfi/` and `output/iaci/` directories exist
3. Run plot generator manually to debug

### Newsletter Issues

#### Problem: "No subscribers found"
**Solution:**
1. Check `subscribers.csv` exists in repository root
2. Verify CSV has `email` column header
3. Ensure at least one valid email address is present

#### Problem: "Newsletter sent but images missing"
**Solution:**
1. Verify charts were generated successfully
2. Check chart file paths in `newsletter_generator.py`
3. Ensure images are embedded with correct Content-ID tags

### Warning Emails

You'll receive a warning email to `hadobrockmeyer@gmail.com` when:
- ❌ WCI email not found in last 14 days
- ❌ IACI email not found in last 14 days
- ❌ SCFI API fails to return data
- ❌ Email found but value/date extraction failed

**Warning Email Format:**
```
Subject: ⚠️ Freight Indices Warning: Data Collection Failed

Freight Indices Scraper Warning

Problem: Data Collection Failed
Details:
• WCI: No email found in last 14 days
• SCFI: API request failed

Date: 2026-02-16 13:00:00
```

---

## 🔧 Maintenance

### Adding Historical Data

To backfill historical data:

1. Edit CSV files in `data/` directory
2. Add rows in DD.MM.YYYY format:
   ```csv
   Date,Value
   01.01.2025,1500
   08.01.2025,1550
   ```
3. Commit and push changes
4. Charts will automatically reflect new data on next run

### Updating Email Recipients

1. Edit `subscribers.csv`
2. Add/remove email addresses
3. Commit and push changes
4. Next newsletter will use updated list

### Changing Newsletter Schedule

Edit cron schedules in `.github/workflows/*.yml` files:

```yaml
schedule:
  - cron: '0 13 * * 5'  # Friday 13:00 UTC
```

**Cron Format:** `minute hour day month weekday`
- `0 13 * * 5` = Every Friday at 13:00 UTC
- `30 12 * * 5` = Every Friday at 12:30 UTC

**Helpful Tool:** https://crontab.guru/

---

## 📚 Dependencies

All Python dependencies are listed in `requirements.txt`:

```txt
beautifulsoup4==4.12.3
pandas==2.2.0
requests==2.31.0
matplotlib==3.8.2
lxml==5.1.0
```

**Installed automatically** by GitHub Actions before each workflow run.

---

## 🛡️ Security Best Practices

1. ✅ **Never commit passwords** - Use GitHub Secrets only
2. ✅ **Use Gmail App Passwords** - Not your actual Gmail password
3. ✅ **Keep repository private** - Protects subscriber emails
4. ✅ **Review commits** - Ensure no sensitive data is exposed
5. ✅ **Rotate App Passwords** - Change periodically for security

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

## 🤝 Contributing

### Reporting Issues
1. Check existing issues in GitHub
2. Create new issue with:
   - Clear description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs/screenshots

### Feature Requests
1. Open a new issue
2. Tag as "enhancement"
3. Describe use case and proposed solution

### Code Contributions
1. Fork repository
2. Create feature branch
3. Make changes with clear commit messages
4. Test thoroughly
5. Submit pull request

---

## 📞 Support

For questions or issues:
- **Email:** hadobrockmeyer@gmail.com (maintainer)
- **GitHub Issues:** https://github.com/YOUR-USERNAME/freight-indices-newsletter/issues

---

## 🎉 Acknowledgments

- **Drewry** - WCI and IACI data source
- **Shanghai Shipping Exchange** - SCFI data API
- **GitHub Actions** - Free CI/CD automation
- **Matplotlib** - Chart generation library

---

**Last Updated:** February 2026  
**Version:** 1.0.0

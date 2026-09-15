import email
from email.header import decode_header
import imaplib
import os
import re
import requests
import smtplib
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import pandas as pd
import logging

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

WCI_CSV = os.path.join(DATA_DIR, "wci.csv")
IACI_CSV = os.path.join(DATA_DIR, "iaci.csv")
SCFI_CSV = os.path.join(DATA_DIR, "scfi.csv")

# Warning email recipient
WARNING_EMAIL = "hadobrockmeyer@gmail.com"


def parse_email_config():
    """Parse EMAIL_CONFIG environment variable."""
    config = os.getenv("EMAIL_CONFIG")
    if not config:
        raise ValueError("EMAIL_CONFIG environment variable not set")
    
    parts = config.split(":")
    if len(parts) != 4:
        raise ValueError("EMAIL_CONFIG must be in format: email:password:smtp_server:port")
    
    return {
        "email": parts[0],
        "password": parts[1],
        "smtp_server": parts[2],
        "smtp_port": int(parts[3])
    }


def send_warning_email(subject, message):
    """Send warning email when data collection fails."""
    logger.warning(f"⚠️ Sending warning email: {subject}")
    
    try:
        config = parse_email_config()
        
        msg = MIMEText(
            f"Freight Indices Scraper Warning\n\n"
            f"Problem: {subject}\n"
            f"Details: {message}\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "plain",
            "utf-8"
        )
        msg["Subject"] = f"⚠️ Freight Indices Warning: {subject}"
        msg["From"] = config["email"]
        msg["To"] = WARNING_EMAIL
        
        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["email"], config["password"])
            server.send_message(msg)
        
        logger.info("✅ Warning email sent successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to send warning email: {str(e)}")


def fetch_wci_email():
    """Fetch latest WCI email from last 14 days."""
    logger.info("🔍 DEBUG - fetch_wci_email: Starting WCI email fetch")
    
    try:
        config = parse_email_config()
        logger.info(f"✅ DEBUG - fetch_wci_email: Connected to mailbox: {config['email']}")
        
        mail = imaplib.IMAP4_SSL(config['smtp_server'].replace('smtp', 'imap'), 993, timeout=30)
        mail.login(config['email'], config['password'])
        logger.info("✅ DEBUG - fetch_wci_email: Successfully logged into mailbox")
        
        result, data = mail.select('inbox')
        if result != 'OK':
            logger.error(f"❌ DEBUG - fetch_wci_email: Failed to select inbox")
            raise Exception(f"IMAP select failed: {result}")
        
        since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        search_criteria = f'FROM noreply@drewry.co.uk SINCE {since_date}'
        logger.info(f"🔍 DEBUG - fetch_wci_email: Searching with criteria: {search_criteria}")
        
        result, data = mail.search(None, search_criteria)
        if result != 'OK':
            logger.error(f"❌ DEBUG - fetch_wci_email: Search failed")
            raise Exception(f"IMAP search failed: {result}")
        
        email_ids = data[0].split()
        logger.info(f"📧 DEBUG - fetch_wci_email: Found {len(email_ids)} emails from Drewry")
        
        if not email_ids:
            logger.warning("⚠️ DEBUG - fetch_wci_email: No WCI emails found in last 14 days")
            mail.logout()
            return None, None
        
        for email_id in email_ids[::-1]:
            result, data = mail.fetch(email_id, '(RFC822)')
            if result != 'OK':
                continue
            
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(email_message['subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')
            
            logger.info(f"📨 DEBUG - fetch_wci_email: Checking email subject: {subject}")
            
            if "World Container Freight Market Update" in subject:
                logger.info(f"✅ DEBUG - fetch_wci_email: Found relevant WCI email: {subject}")
                
                html_content = None
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == 'text/html':
                            html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    if email_message.get_content_type() == 'text/html':
                        html_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                if html_content:
                    logger.info("✅ DEBUG - fetch_wci_email: Successfully extracted HTML content")
                    mail.logout()
                    return html_content, subject
        
        logger.warning("⚠️ DEBUG - fetch_wci_email: No matching WCI email found")
        mail.logout()
        return None, None
        
    except Exception as e:
        logger.error(f"❌ DEBUG - fetch_wci_email: Error: {str(e)}")
        if 'mail' in locals():
            mail.logout()
        return None, None


def extract_wci_from_html(html_content, subject):
    """Extract WCI value and date from HTML."""
    logger.info("🔍 DEBUG - extract_wci_from_html: Parsing HTML content")
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(strip=True)
        
        wci_match = re.search(r'\(WCI\)[^$]*\$(\d{1,3}(?:,\d{3})*)\s*per 40ft container', text)
        if not wci_match:
            logger.error("❌ DEBUG - extract_wci_from_html: Could not extract WCI value")
            return None, None

        wci_value = float(wci_match.group(1).replace(',', ''))
        logger.info(f"✅ DEBUG - extract_wci_from_html: Extracted WCI value: ${wci_value:.2f}")
        
        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', subject or text)
        wci_date = None
        if date_match:
            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    wci_date = datetime.strptime(date_match.group(1), fmt).strftime("%d.%m.%Y")
                    break
                except ValueError:
                    continue
        
        if wci_date is None:
            wci_date = datetime.now().strftime("%d.%m.%Y")
            logger.warning(f"⚠️ DEBUG - extract_wci_from_html: Could not parse date, using today: {wci_date}")
        else:
            logger.info(f"✅ DEBUG - extract_wci_from_html: Extracted date: {wci_date}")
        
        return wci_value, wci_date
        
    except Exception as e:
        logger.error(f"❌ DEBUG - extract_wci_from_html: Error: {str(e)}")
        return None, None


def fetch_iaci_email():
    """Fetch latest IACI email from last 14 days."""
    logger.info("🔍 DEBUG - fetch_iaci_email: Starting IACI email fetch")
    
    try:
        config = parse_email_config()
        logger.info(f"✅ DEBUG - fetch_iaci_email: Connected to mailbox: {config['email']}")
        
        mail = imaplib.IMAP4_SSL(config['smtp_server'].replace('smtp', 'imap'), 993, timeout=30)
        mail.login(config['email'], config['password'])
        logger.info("✅ DEBUG - fetch_iaci_email: Successfully logged into mailbox")
        
        result, data = mail.select('inbox')
        if result != 'OK':
            logger.error(f"❌ DEBUG - fetch_iaci_email: Failed to select inbox")
            raise Exception(f"IMAP select failed: {result}")
        
        since_date = (datetime.now() - timedelta(days=14)).strftime("%d-%b-%Y")
        search_criteria = f'FROM noreply@drewry.co.uk SINCE {since_date}'
        logger.info(f"🔍 DEBUG - fetch_iaci_email: Searching with criteria: {search_criteria}")
        
        result, data = mail.search(None, search_criteria)
        if result != 'OK':
            logger.error(f"❌ DEBUG - fetch_iaci_email: Search failed")
            raise Exception(f"IMAP search failed: {result}")
        
        email_ids = data[0].split()
        logger.info(f"📧 DEBUG - fetch_iaci_email: Found {len(email_ids)} emails from Drewry")
        
        if not email_ids:
            logger.warning("⚠️ DEBUG - fetch_iaci_email: No IACI emails found in last 14 days")
            mail.logout()
            return None, None
        
        for email_id in email_ids[::-1]:
            result, data = mail.fetch(email_id, '(RFC822)')
            if result != 'OK':
                continue
            
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            subject, encoding = decode_header(email_message['subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')
            
            logger.info(f"📨 DEBUG - fetch_iaci_email: Checking email subject: {subject}")
            
            if "World Container Freight Market Update" in subject:
                logger.info(f"✅ DEBUG - fetch_iaci_email: Found relevant IACI email: {subject}")
                
                html_content = None
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == 'text/html':
                            html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    if email_message.get_content_type() == 'text/html':
                        html_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                if html_content:
                    logger.info("✅ DEBUG - fetch_iaci_email: Successfully extracted HTML content")
                    mail.logout()
                    return html_content, subject
        
        logger.warning("⚠️ DEBUG - fetch_iaci_email: No matching IACI email found")
        mail.logout()
        return None, None
        
    except Exception as e:
        logger.error(f"❌ DEBUG - fetch_iaci_email: Error: {str(e)}")
        if 'mail' in locals():
            mail.logout()
        return None, None


def extract_iaci_from_html(html_content, subject):
    """Extract IACI value and date from HTML."""
    logger.info("🔍 DEBUG - extract_iaci_from_html: Parsing HTML content")
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(strip=True)
        
        iaci_match = re.search(r'\(IACI\)[^$]*\$(\d{1,3}(?:,\d{3})*)\s*per 40ft container', text)
        if not iaci_match:
            logger.error("❌ DEBUG - extract_iaci_from_html: Could not extract IACI value")
            return None, None

        iaci_value = float(iaci_match.group(1).replace(',', ''))
        logger.info(f"✅ DEBUG - extract_iaci_from_html: Extracted IACI value: ${iaci_value:.2f}")
        
        date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', subject or text)
        iaci_date = None
        if date_match:
            for fmt in ["%d %B %Y", "%d %b %Y"]:
                try:
                    iaci_date = datetime.strptime(date_match.group(1), fmt).strftime("%d.%m.%Y")
                    break
                except ValueError:
                    continue
        
        if iaci_date is None:
            iaci_date = datetime.now().strftime("%d.%m.%Y")
            logger.warning(f"⚠️ DEBUG - extract_iaci_from_html: Could not parse date, using today: {iaci_date}")
        else:
            logger.info(f"✅ DEBUG - extract_iaci_from_html: Extracted date: {iaci_date}")
        
        return iaci_value, iaci_date
        
    except Exception as e:
        logger.error(f"❌ DEBUG - extract_iaci_from_html: Error: {str(e)}")
        return None, None


def fetch_scfi():
    """Fetch SCFI data from SSE API."""
    logger.info("🔍 DEBUG - fetch_scfi: Starting SCFI fetch from SSE API")
    
    url = "https://en.sse.net.cn/currentIndex?indexName=scfi"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        logger.info(f"🔍 DEBUG - fetch_scfi: Requesting URL: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("✅ DEBUG - fetch_scfi: Successfully received API response")
        
        if data.get("status") == 0:
            logger.error(f"❌ DEBUG - fetch_scfi: API error: {data.get('msg')}")
            return None, None
        
        scfi_data = data.get("data", {})
        current_date = scfi_data.get("currentDate")
        line_data_list = scfi_data.get("lineDataList", [])
        
        if not line_data_list:
            logger.error("❌ DEBUG - fetch_scfi: No lineDataList in API response")
            return None, None
        
        scfi_value = float(line_data_list[0]["currentContent"])
        logger.info(f"✅ DEBUG - fetch_scfi: Extracted SCFI value: {scfi_value:.2f}")
        
        scfi_date = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                scfi_date = datetime.strptime(current_date, fmt).strftime("%d.%m.%Y")
                break
            except ValueError:
                continue
        
        if scfi_date is None:
            scfi_date = datetime.now().strftime("%d.%m.%Y")
            logger.warning(f"⚠️ DEBUG - fetch_scfi: Could not parse date '{current_date}', using today: {scfi_date}")
        else:
            logger.info(f"✅ DEBUG - fetch_scfi: Extracted date: {scfi_date}")
        
        return scfi_value, scfi_date
        
    except Exception as e:
        logger.error(f"❌ DEBUG - fetch_scfi: Error: {str(e)}")
        return None, None


def load_csv(filepath):
    """Load CSV or create empty one."""
    logger.info(f"🔍 DEBUG - load_csv: Loading {filepath}")
    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        logger.info(f"✅ DEBUG - load_csv: Loaded {len(df)} existing records from {os.path.basename(filepath)}")
        return df
    else:
        logger.info(f"⚠️ DEBUG - load_csv: File {os.path.basename(filepath)} does not exist, creating new")
        return pd.DataFrame(columns=["Date", "Value"])


def save_csv(df, filepath):
    """Save CSV file."""
    df.to_csv(filepath, index=False)
    logger.info(f"✅ DEBUG - save_csv: Saved {len(df)} records to {os.path.basename(filepath)}")


def update_data(value, date_str, csv_path, name):
    """Update CSV with new value."""
    logger.info(f"🔍 DEBUG - update_data: Checking if {name} data needs update")
    
    if value is None or date_str is None:
        logger.warning(f"⚠️ DEBUG - update_data: {name} - No new data available, skipping update")
        return False
    
    df = load_csv(csv_path)
    
    if date_str in df['Date'].values:
        existing_value = df[df['Date'] == date_str]['Value'].values[0]
        if existing_value == value:
            logger.info(f"✅ DEBUG - update_data: {name} - Date {date_str} already exists with same value ({value})")
            return False
        else:
            logger.info(f"🔄 DEBUG - update_data: {name} - Updating value for {date_str}: {existing_value} → {value}")
            df.loc[df['Date'] == date_str, 'Value'] = value
    else:
        logger.info(f"➕ DEBUG - update_data: {name} - Adding new record: {date_str} = {value}")
        new_row = pd.DataFrame([{"Date": date_str, "Value": value}])
        df = pd.concat([df, new_row], ignore_index=True)
    
    save_csv(df, csv_path)
    return True


def run_scraper():
    """Main scraper function with warning emails."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Freight Indices Scraper")
    logger.info("=" * 80)
    
    warnings = []
    
    # WCI scraping
    logger.info("\n📦 WCI - World Container Index")
    logger.info("-" * 80)
    wci_html, wci_subject = fetch_wci_email()
    if wci_html:
        wci_value, wci_date = extract_wci_from_html(wci_html, wci_subject)
        if wci_value is None or wci_date is None:
            warnings.append("WCI: Email found but could not extract value/date")
        else:
            update_data(wci_value, wci_date, WCI_CSV, "WCI")
    else:
        warnings.append("WCI: No email found in last 14 days")
        logger.warning("⚠️ WCI: No email data available")
    
    # IACI scraping
    logger.info("\n📦 IACI - Intra-Asia Container Index")
    logger.info("-" * 80)
    iaci_html, iaci_subject = fetch_iaci_email()
    if iaci_html:
        iaci_value, iaci_date = extract_iaci_from_html(iaci_html, iaci_subject)
        if iaci_value is None or iaci_date is None:
            warnings.append("IACI: Email found but could not extract value/date")
        else:
            update_data(iaci_value, iaci_date, IACI_CSV, "IACI")
    else:
        warnings.append("IACI: No email found in last 14 days")
        logger.warning("⚠️ IACI: No email data available")
    
    # SCFI scraping
    logger.info("\n📦 SCFI - Shanghai Containerized Freight Index")
    logger.info("-" * 80)
    scfi_value, scfi_date = fetch_scfi()
    if scfi_value is None or scfi_date is None:
        warnings.append("SCFI: API request failed or could not extract value/date")
        logger.warning("⚠️ SCFI: No data available")
    else:
        update_data(scfi_value, scfi_date, SCFI_CSV, "SCFI")
    
    # Send warning email if any failures
    if warnings:
        logger.warning(f"\n⚠️ {len(warnings)} warning(s) detected:")
        for w in warnings:
            logger.warning(f"  - {w}")
        
        warning_message = "\n".join(f"• {w}" for w in warnings)
        send_warning_email("Data Collection Failed", warning_message)
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Scraper finished")
    logger.info("=" * 80)


if __name__ == "__main__":
    run_scraper()

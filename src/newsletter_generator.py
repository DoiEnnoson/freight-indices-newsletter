#!/usr/bin/env python3
"""
Freight Indices Newsletter Generator
=====================================

Generates weekly HTML newsletter with:
- WCI vs SCFI chart
- IACI chart
- Weekly performance table with YoY comparison
"""

import os
import pandas as pd
import smtplib
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'output'
CHART_WCI_SCFI = OUTPUT_DIR / 'wci_scfi' / 'wci_scfi_chart.png'
CHART_IACI = OUTPUT_DIR / 'iaci' / 'iaci_chart.png'
HTML_TEMPLATE = BASE_DIR / 'html_template.html'
OUTPUT_HTML = BASE_DIR / 'newsletter.html'
SUBSCRIBERS_CSV = BASE_DIR / 'subscribers.csv'

# Threshold for change direction
THRESHOLD_NEUTRAL = 1.0  # ±1.0% = stable


def parse_email_config():
    """Parse EMAIL_CONFIG environment variable."""
    config = os.getenv("EMAIL_CONFIG")
    if not config:
        raise ValueError("EMAIL_CONFIG environment variable not set")
    
    # Format: email:password:smtp_server:port
    parts = config.split(":")
    if len(parts) != 4:
        raise ValueError("EMAIL_CONFIG must be in format: email:password:smtp_server:port")
    
    return {
        "email": parts[0],
        "password": parts[1],
        "smtp_server": parts[2],
        "smtp_port": int(parts[3])
    }


def load_subscribers():
    """Load subscriber email addresses from CSV."""
    if not SUBSCRIBERS_CSV.exists():
        logger.warning(f"⚠️ Subscribers file not found: {SUBSCRIBERS_CSV}")
        logger.warning("⚠️ Create subscribers.csv with 'email' column")
        return []
    
    try:
        df = pd.read_csv(SUBSCRIBERS_CSV)
        
        if 'email' not in df.columns:
            logger.error("❌ subscribers.csv must have 'email' column")
            return []
        
        # Remove empty emails and duplicates
        emails = df['email'].dropna().str.strip().unique().tolist()
        
        logger.info(f"✅ Loaded {len(emails)} subscriber(s)")
        for email in emails:
            logger.info(f"   📧 {email}")
        
        return emails
        
    except Exception as e:
        logger.error(f"❌ Error loading subscribers: {str(e)}")
        return []


def load_index_data(csv_file):
    """Load index data from CSV file."""
    filepath = DATA_DIR / csv_file
    
    if not filepath.exists():
        logger.warning(f"⚠️ File not found: {csv_file}")
        return None
    
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y')
    df = df.sort_values('Date')
    
    return df


def calculate_changes(df):
    """Calculate week-over-week and year-over-year changes."""
    if df is None or len(df) < 2:
        return None, None, None, None
    
    latest = df.iloc[-1]
    current_value = latest['Value']
    current_date = latest['Date']
    
    # Week change (7 days ago)
    week_ago = current_date - timedelta(days=7)
    week_df = df[df['Date'] <= week_ago]
    
    if len(week_df) > 0:
        week_value = week_df.iloc[-1]['Value']
        week_change = ((current_value - week_value) / week_value) * 100
    else:
        week_change = None
    
    # Year-over-year change (365 days ago)
    year_ago = current_date - timedelta(days=365)
    year_df = df[df['Date'] <= year_ago]
    
    if len(year_df) > 0:
        year_value = year_df.iloc[-1]['Value']
        yoy_change = ((current_value - year_value) / year_value) * 100
    else:
        yoy_change = None
    
    return current_value, current_date, week_change, yoy_change


def format_change(change_pct):
    """Format change with direction symbol and color."""
    if change_pct is None:
        return "N/A", "change-neutral"
    
    if change_pct > THRESHOLD_NEUTRAL:
        symbol = '▲'
        css_class = 'change-positive'
    elif change_pct < -THRESHOLD_NEUTRAL:
        symbol = '▼'
        css_class = 'change-negative'
    else:
        symbol = '●'
        css_class = 'change-neutral'
    
    return f"{symbol} {change_pct:+.1f}%", css_class


def generate_table_rows():
    """Generate HTML table rows for all indices."""
    logger.info("📊 Generating performance table")
    
    indices = {
        'WCI': 'wci.csv',
        'SCFI': 'scfi.csv',
        'IACI': 'iaci.csv'
    }
    
    rows = []
    
    for name, filename in indices.items():
        df = load_index_data(filename)
        current_value, current_date, week_change, yoy_change = calculate_changes(df)
        
        if current_value is None:
            logger.warning(f"⚠️ No data for {name}")
            continue
        
        # Format values
        value_str = f"${current_value:,.0f}"  # No decimal places
        date_str = current_date.strftime('%b %d, %Y')
        
        week_str, week_class = format_change(week_change)
        yoy_str, yoy_class = format_change(yoy_change)
        
        row = f"""
                        <tr>
                            <td class="index-name">{name}</td>
                            <td class="price">{value_str}</td>
                            <td class="price {week_class}">{week_str}</td>
                            <td class="price {yoy_class}">{yoy_str}</td>
                            <td>{date_str}</td>
                        </tr>"""
        
        rows.append(row)
        logger.info(f"  ✅ {name}: {value_str} (Week: {week_str}, YoY: {yoy_str})")
    
    return '\n'.join(rows)


def generate_newsletter_html():
    """Generate newsletter HTML file."""
    logger.info("=" * 80)
    logger.info("📧 Freight Indices Newsletter Generator")
    logger.info("=" * 80)
    
    # Check if template exists
    if not HTML_TEMPLATE.exists():
        raise FileNotFoundError(f"HTML template not found: {HTML_TEMPLATE}")
    
    # Check if charts exist
    if not CHART_WCI_SCFI.exists():
        raise FileNotFoundError(f"WCI/SCFI chart not found: {CHART_WCI_SCFI}")
    
    if not CHART_IACI.exists():
        raise FileNotFoundError(f"IACI chart not found: {CHART_IACI}")
    
    logger.info("📄 Loading HTML template")
    with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    logger.info("📊 Generating table rows")
    table_rows = generate_table_rows()
    
    logger.info("🔧 Assembling newsletter")
    today = datetime.now().strftime('%B %d, %Y')
    
    newsletter = template.replace('{{DATE}}', today)
    newsletter = newsletter.replace('{{TABLE_ROWS}}', table_rows)
    
    # Save newsletter
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(newsletter)
    
    logger.info(f"✅ Newsletter HTML saved: {OUTPUT_HTML}")
    logger.info("=" * 80)
    
    return OUTPUT_HTML


def send_newsletter():
    """Send newsletter via email to all subscribers."""
    logger.info("📧 Preparing to send newsletter")
    
    # Load subscribers
    subscribers = load_subscribers()
    
    if not subscribers:
        logger.error("❌ No subscribers found, aborting")
        return False
    
    # Generate HTML
    html_file = generate_newsletter_html()
    
    # Parse email config
    config = parse_email_config()
    
    # Read HTML content
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Read chart images
    with open(CHART_WCI_SCFI, 'rb') as f:
        wci_scfi_img = f.read()
    
    with open(CHART_IACI, 'rb') as f:
        iaci_img = f.read()
    
    # Send to each subscriber
    logger.info(f"📤 Sending newsletter to {len(subscribers)} subscriber(s)")
    
    success_count = 0
    fail_count = 0
    
    try:
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['email'], config['password'])
            logger.info(f"✅ Connected to {config['smtp_server']}")
            
            for subscriber_email in subscribers:
                try:
                    # Create email message for each subscriber
                    msg = MIMEMultipart('related')
                    msg['Subject'] = f"Weekly Freight Indices Newsletter - {datetime.now().strftime('%B %d, %Y')}"
                    msg['From'] = config['email']
                    msg['To'] = subscriber_email
                    
                    # Attach HTML
                    msg_html = MIMEText(html_content, 'html', 'utf-8')
                    msg.attach(msg_html)
                    
                    # Attach charts
                    img1 = MIMEImage(wci_scfi_img)
                    img1.add_header('Content-ID', '<chart_wci_scfi>')
                    msg.attach(img1)
                    
                    img2 = MIMEImage(iaci_img)
                    img2.add_header('Content-ID', '<chart_iaci>')
                    msg.attach(img2)
                    
                    # Send
                    server.send_message(msg)
                    logger.info(f"  ✅ Sent to {subscriber_email}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"  ❌ Failed to send to {subscriber_email}: {str(e)}")
                    fail_count += 1
        
        logger.info("=" * 80)
        logger.info(f"✅ Newsletter sending complete!")
        logger.info(f"   Success: {success_count}")
        logger.info(f"   Failed: {fail_count}")
        logger.info("=" * 80)
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to SMTP server: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        send_newsletter()
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        exit(1)

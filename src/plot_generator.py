import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
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
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

WCI_SCFI_OUTPUT = os.path.join(OUTPUT_DIR, "wci_scfi", "wci_scfi_chart.png")
IACI_OUTPUT = os.path.join(OUTPUT_DIR, "iaci", "iaci_chart.png")
WCI_WEB_OUTPUT = os.path.join(BASE_DIR, "docs", "wci_chart.png")  # Signup page (GitHub Pages)

# Colors
COLOR_WCI = "#0E2841"  # Dark blue
COLOR_SCFI = "#AAD228"  # Light green
COLOR_IACI = "#0E2841"  # Dark blue

# Font settings
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']


def load_and_prepare_data(csv_path, date_col='Date', value_col='Value'):
    """Load CSV and prepare data for plotting."""
    logger.info(f"📂 Loading data from {os.path.basename(csv_path)}")
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ File not found: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    logger.info(f"✅ Loaded {len(df)} records")
    
    # Convert date column to datetime (DD.MM.YYYY format)
    df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='coerce')
    
    # Remove rows with invalid dates
    df = df.dropna(subset=[date_col])
    
    # Sort by date
    df = df.sort_values(date_col)
    
    logger.info(f"✅ Date range: {df[date_col].min()} to {df[date_col].max()}")
    logger.info(f"✅ Valid records after parsing: {len(df)}")
    
    return df


def create_wci_scfi_chart():
    """Create combined WCI and SCFI chart."""
    logger.info("📊 Creating WCI vs SCFI chart")
    
    # Load data
    wci_df = load_and_prepare_data(os.path.join(DATA_DIR, "wci.csv"))
    scfi_df = load_and_prepare_data(os.path.join(DATA_DIR, "scfi.csv"))
    
    if wci_df is None or scfi_df is None:
        logger.error("❌ Could not load data for WCI/SCFI chart")
        return False
    
    # Filter data from 2025-01-01 onwards
    start_date = pd.Timestamp('2025-01-01')
    wci_df = wci_df[wci_df['Date'] >= start_date]
    scfi_df = scfi_df[scfi_df['Date'] >= start_date]
    
    logger.info(f"📊 WCI records after filtering: {len(wci_df)}")
    logger.info(f"📊 SCFI records after filtering: {len(scfi_df)}")
    
    if len(wci_df) == 0:
        logger.warning("⚠️ No WCI data available from 2025-01-01")
    if len(scfi_df) == 0:
        logger.warning("⚠️ No SCFI data available from 2025-01-01")
    
    # Create figure with single y-axis
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot both on same y-axis (both in USD)
    ax.plot(wci_df['Date'], wci_df['Value'], 
            color=COLOR_WCI, linewidth=2.5, label='WCI', marker='o', markersize=4)
    ax.plot(scfi_df['Date'], scfi_df['Value'], 
            color=COLOR_SCFI, linewidth=2.5, label='SCFI', marker='s', markersize=4)
    
    ax.set_xlabel('')  # Remove "Date" label
    ax.set_ylabel('USD per 40ft container', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis with week numbers
    ax.xaxis.set_major_formatter(mdates.DateFormatter('W%V %Y'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=4))  # Every 4 weeks
    
    # Get the last dates and values
    if len(wci_df) > 0:
        last_wci_date = wci_df['Date'].iloc[-1]
        last_wci_value = wci_df['Value'].iloc[-1]
        
        # Annotate WCI value with white background box (no arrow)
        ax.annotate(f'WCI: ${last_wci_value:.0f}', 
                   xy=(last_wci_date, last_wci_value),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, fontweight='bold', color=COLOR_WCI,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=COLOR_WCI, linewidth=2))
    
    if len(scfi_df) > 0:
        last_scfi_date = scfi_df['Date'].iloc[-1]
        last_scfi_value = scfi_df['Value'].iloc[-1]
        
        # Annotate SCFI value with white background box (no arrow, offset differently to avoid overlap)
        ax.annotate(f'SCFI: ${last_scfi_value:.0f}', 
                   xy=(last_scfi_date, last_scfi_value),
                   xytext=(10, -25), textcoords='offset points',
                   fontsize=10, fontweight='bold', color=COLOR_SCFI,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=COLOR_SCFI, linewidth=2))
    
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and subtitle
    current_date = datetime.now().strftime('%B %d, %Y')
    fig.suptitle('WCI vs. SCFI', fontsize=18, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, f'Generated: {current_date}  |  Source: Drewry, Shanghai Shipping Exchange',
             ha='center', fontsize=11, style='normal')
    
    # Copyright
    fig.text(0.98, 0.98, '© Dói Ennoson', ha='right', va='top', fontsize=9, style='italic')
    
    # Legend
    ax.legend(loc='upper left', fontsize=11)
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    os.makedirs(os.path.dirname(WCI_SCFI_OUTPUT), exist_ok=True)
    plt.savefig(WCI_SCFI_OUTPUT, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ WCI/SCFI chart saved to {WCI_SCFI_OUTPUT}")
    return True


def create_iaci_chart():
    """Create IACI chart."""
    logger.info("📊 Creating IACI chart")
    
    # Load data
    iaci_df = load_and_prepare_data(os.path.join(DATA_DIR, "iaci.csv"))
    
    if iaci_df is None:
        logger.error("❌ Could not load data for IACI chart")
        return False
    
    logger.info(f"📊 IACI records: {len(iaci_df)}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot IACI
    ax.plot(iaci_df['Date'], iaci_df['Value'], 
            color=COLOR_IACI, linewidth=2.5, marker='o', markersize=4)
    ax.set_xlabel('')  # Remove "Date" label
    ax.set_ylabel('IACI (USD per 40ft container)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    
    # Set x-axis limits to actual data range
    if len(iaci_df) > 0:
        ax.set_xlim(iaci_df['Date'].min(), iaci_df['Date'].max())
    
    # Get the last date and always show it with actual date
    if len(iaci_df) > 0:
        last_date = iaci_df['Date'].iloc[-1]
        last_value = iaci_df['Value'].iloc[-1]
        
        # Get current tick locations and labels
        current_ticks = list(ax.get_xticks())
        current_labels = [label.get_text() for label in ax.get_xticklabels()]
        
        # Convert last_date to matplotlib date number
        last_date_num = mdates.date2num(last_date)
        
        # Add last date to ticks if not already there
        if last_date_num not in current_ticks:
            current_ticks.append(last_date_num)
            ax.set_xticks(current_ticks)
            
            # Format labels: all others as "Mon YYYY", last one as "DD Mon YYYY"
            labels = []
            for tick in current_ticks:
                tick_date = mdates.num2date(tick)
                if abs(tick - last_date_num) < 0.5:  # This is the last date
                    labels.append(tick_date.strftime('%d %b %Y'))
                else:
                    labels.append(tick_date.strftime('%b %Y'))
            ax.set_xticklabels(labels)
        
        # Add value annotation for last point (no arrow)
        ax.annotate(f'${last_value:.0f}', 
                   xy=(last_date, last_value),
                   xytext=(10, 10), textcoords='offset points',
                   fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor=COLOR_IACI, linewidth=2))
    
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and subtitle
    current_date = datetime.now().strftime('%B %d, %Y')
    fig.suptitle('Intra-Asia Container Index', fontsize=18, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, f'Generated: {current_date}  |  Source: Drewry',
             ha='center', fontsize=11, style='normal')
    
    # Copyright
    fig.text(0.98, 0.98, '© Dói Ennoson', ha='right', va='top', fontsize=9, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    os.makedirs(os.path.dirname(IACI_OUTPUT), exist_ok=True)
    plt.savefig(IACI_OUTPUT, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"✅ IACI chart saved to {IACI_OUTPUT}")
    return True


def create_wci_web_chart():
    """Create compact WCI chart (last 12 months) for the signup page."""
    logger.info("📊 Creating WCI chart for signup page")
    
    wci_df = load_and_prepare_data(os.path.join(DATA_DIR, "wci.csv"))
    if wci_df is None or len(wci_df) == 0:
        logger.error("❌ Could not load data for WCI web chart")
        return False
    
    start_date = wci_df['Date'].max() - pd.DateOffset(months=12)
    wci_df = wci_df[wci_df['Date'] >= start_date]
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    ax.plot(wci_df['Date'], wci_df['Value'], color=COLOR_WCI, linewidth=2.5)
    ax.fill_between(wci_df['Date'], wci_df['Value'], wci_df['Value'].min() * 0.9,
                    color=COLOR_WCI, alpha=0.08)
    ax.set_ylim(bottom=wci_df['Value'].min() * 0.9)
    
    # Highlight latest value
    last_date = wci_df['Date'].iloc[-1]
    last_value = wci_df['Value'].iloc[-1]
    ax.scatter([last_date], [last_value], color=COLOR_SCFI, edgecolor=COLOR_WCI, s=60, zorder=3)
    ax.annotate(f'${last_value:,.0f}\n{last_date.strftime("%d %b %Y")}',
                xy=(last_date, last_value), xytext=(-10, 12), textcoords='offset points',
                ha='right', fontsize=10, fontweight='bold', color=COLOR_WCI)
    
    ax.set_ylabel('USD per 40ft container', fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9)
    
    ax.set_title('Drewry World Container Index (WCI), last 12 months',
                 fontsize=13, fontweight='bold', color=COLOR_WCI, loc='left')
    fig.text(0.99, 0.01, 'Source: Drewry  |  © Dói Ennoson', ha='right', va='bottom', fontsize=8, style='italic')
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    os.makedirs(os.path.dirname(WCI_WEB_OUTPUT), exist_ok=True)
    plt.savefig(WCI_WEB_OUTPUT, dpi=160, facecolor='white')
    plt.close()
    
    logger.info(f"✅ WCI web chart saved to {WCI_WEB_OUTPUT}")
    return True


def generate_all_plots():
    """Generate all plots."""
    logger.info("=" * 80)
    logger.info("📊 Starting Plot Generation")
    logger.info("=" * 80)
    
    success = True
    
    # Generate WCI/SCFI chart
    if not create_wci_scfi_chart():
        success = False
        logger.error("❌ Failed to create WCI/SCFI chart")
    
    # Generate IACI chart
    if not create_iaci_chart():
        success = False
        logger.error("❌ Failed to create IACI chart")
    
    # Generate WCI chart for the signup page
    if not create_wci_web_chart():
        success = False
        logger.error("❌ Failed to create WCI web chart")
    
    logger.info("=" * 80)
    if success:
        logger.info("✅ All plots generated successfully")
    else:
        logger.warning("⚠️ Some plots failed to generate")
    logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    generate_all_plots()

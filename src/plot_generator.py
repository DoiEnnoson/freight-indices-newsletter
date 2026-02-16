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
    
    # Convert date column to datetime
    df[date_col] = pd.to_datetime(df[date_col], format='%d.%m.%Y', errors='coerce')
    
    # Remove rows with invalid dates
    df = df.dropna(subset=[date_col])
    
    # Sort by date
    df = df.sort_values(date_col)
    
    logger.info(f"✅ Date range: {df[date_col].min()} to {df[date_col].max()}")
    
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
    
    # Create figure
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Plot WCI on primary y-axis
    ax1.plot(wci_df['Date'], wci_df['Value'], 
             color=COLOR_WCI, linewidth=2.5, label='WCI', marker='o', markersize=4)
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('WCI (USD per 40ft container)', fontsize=12, fontweight='bold', color=COLOR_WCI)
    ax1.tick_params(axis='y', labelcolor=COLOR_WCI)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Create secondary y-axis for SCFI
    ax2 = ax1.twinx()
    ax2.plot(scfi_df['Date'], scfi_df['Value'], 
             color=COLOR_SCFI, linewidth=2.5, label='SCFI', marker='s', markersize=4)
    ax2.set_ylabel('SCFI (Index Points)', fontsize=12, fontweight='bold', color=COLOR_SCFI)
    ax2.tick_params(axis='y', labelcolor=COLOR_SCFI)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator())
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and subtitle
    current_date = datetime.now().strftime('%B %d, %Y')
    fig.suptitle('WCI vs. SCFI', fontsize=18, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, f'Generated: {current_date}  |  Source: Drewry, Shanghai Shipping Exchange',
             ha='center', fontsize=11, style='normal')
    
    # Copyright
    fig.text(0.98, 0.98, '© Dói Ennoson', ha='right', va='top', fontsize=9, style='italic')
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11)
    
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
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('IACI (USD per 40ft container)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
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
    
    logger.info("=" * 80)
    if success:
        logger.info("✅ All plots generated successfully")
    else:
        logger.warning("⚠️ Some plots failed to generate")
    logger.info("=" * 80)
    
    return success


if __name__ == "__main__":
    generate_all_plots()

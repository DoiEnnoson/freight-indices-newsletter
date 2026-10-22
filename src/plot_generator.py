import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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


def style_chart(fig, ax, title, source):
    """Apply the common chart style (title, axes, grid, source line)."""
    ax.set_ylabel('USD per 40ft container', fontsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'${v:,.0f}'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=9)
    
    ax.set_title(title, fontsize=13, fontweight='bold', color=COLOR_WCI, loc='left')
    fig.text(0.99, 0.01, f'Source: {source}  |  © Dói Ennoson', ha='right', va='bottom', fontsize=8, style='italic')
    plt.tight_layout(rect=[0, 0.03, 1, 1])


def mark_last_value(ax, df, color, label='', side='above', x_col='Date', date_format='%d %b %Y', dot_color=COLOR_SCFI):
    """Highlight the latest data point with a dot and its value ('above' or 'right' of the dot)."""
    last_date = df[x_col].iloc[-1]
    last_value = df['Value'].iloc[-1]
    ax.scatter([last_date], [last_value], color=dot_color, edgecolor=color, s=60, zorder=3)
    if side == 'right':
        offset, ha, va = (10, 0), 'left', 'center'
    else:
        offset, ha, va = (-10, 12), 'right', 'bottom'
    ax.annotate(f'{label}${last_value:,.0f}\n{last_date.strftime(date_format)}',
                xy=(last_date, last_value), xytext=offset, textcoords='offset points',
                ha=ha, va=va, fontsize=10, fontweight='bold', color=COLOR_WCI)


def plot_single_index(df, output_path, title, source):
    """Line chart with light area fill for a single index."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    bottom = df['Value'].min() * 0.9
    ax.plot(df['Date'], df['Value'], color=COLOR_WCI, linewidth=2.5)
    ax.fill_between(df['Date'], df['Value'], bottom, color=COLOR_WCI, alpha=0.08)
    ax.set_ylim(bottom=bottom)
    mark_last_value(ax, df, COLOR_WCI)
    
    style_chart(fig, ax, title, source)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=160, facecolor='white')
    plt.close()


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
    
    if len(wci_df) == 0 or len(scfi_df) == 0:
        logger.error("❌ No WCI or SCFI data available from 2025-01-01")
        return False
    
    # Align both indices by calendar week: WCI is published on Thursday, SCFI on Friday,
    # so each week's values share one x position (Monday of the ISO week)
    for df in (wci_df, scfi_df):
        df['Week'] = df['Date'] - pd.to_timedelta(df['Date'].dt.weekday, unit='D')
    wci_df = wci_df.drop_duplicates('Week', keep='last')
    scfi_df = scfi_df.drop_duplicates('Week', keep='last')
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    
    # Both in USD on the same axis
    ax.plot(wci_df['Week'], wci_df['Value'], color=COLOR_WCI, linewidth=2.5)
    ax.plot(scfi_df['Week'], scfi_df['Value'], color=COLOR_SCFI, linewidth=2.5)
    bottom = min(wci_df['Value'].min(), scfi_df['Value'].min()) * 0.9
    ax.set_ylim(bottom=bottom)
    
    # Shading: green below SCFI, blue between SCFI and WCI. Weeks missing in one series
    # (e.g. SCFI holiday breaks) are interpolated, edges take the nearest value.
    weeks = pd.merge(wci_df[['Week', 'Value']], scfi_df[['Week', 'Value']],
                     on='Week', how='outer', suffixes=('_wci', '_scfi')).sort_values('Week')
    weeks = weeks.set_index('Week').interpolate(method='time').ffill().bfill()
    ax.fill_between(weeks.index, weeks['Value_scfi'], bottom, color=COLOR_SCFI, alpha=0.15)
    ax.fill_between(weeks.index, weeks['Value_wci'], weeks['Value_scfi'], color=COLOR_WCI, alpha=0.08)
    
    # Direct labels right of the line ends instead of a legend; extra space on the right for them
    last_week = weeks.index.max()
    first_week = weeks.index.min()
    ax.set_xlim(left=first_week - pd.Timedelta(days=7), right=last_week + (last_week - first_week) * 0.12)
    mark_last_value(ax, wci_df, COLOR_WCI, 'WCI ', side='right', x_col='Week', date_format='W%V', dot_color=COLOR_WCI)
    mark_last_value(ax, scfi_df, COLOR_SCFI, 'SCFI ', side='right', x_col='Week', date_format='W%V')
    
    style_chart(fig, ax, 'WCI vs. SCFI since January 2025', 'Drewry, Shanghai Shipping Exchange')
    # Calendar week labels every 8 weeks, none in the empty label area right of the data
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=8))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('W%V'))
    ax.set_xticks([t for t in ax.get_xticks() if t <= mdates.date2num(last_week)])
    os.makedirs(os.path.dirname(WCI_SCFI_OUTPUT), exist_ok=True)
    plt.savefig(WCI_SCFI_OUTPUT, dpi=160, facecolor='white')
    plt.close()
    
    logger.info(f"✅ WCI/SCFI chart saved to {WCI_SCFI_OUTPUT}")
    return True


def create_iaci_chart():
    """Create IACI chart."""
    logger.info("📊 Creating IACI chart")
    
    iaci_df = load_and_prepare_data(os.path.join(DATA_DIR, "iaci.csv"))
    if iaci_df is None or len(iaci_df) == 0:
        logger.error("❌ Could not load data for IACI chart")
        return False
    
    plot_single_index(iaci_df, IACI_OUTPUT, 'Drewry Intra-Asia Container Index (IACI)', 'Drewry')
    
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
    plot_single_index(wci_df, WCI_WEB_OUTPUT, 'Drewry World Container Index (WCI), last 12 months', 'Drewry')
    
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

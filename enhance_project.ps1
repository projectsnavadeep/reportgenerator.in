# =====================================================
# SAFE AI PROJECT ENHANCEMENT SCRIPT (WINDOWS SAFE)
# Creates business_context.py without touching existing code
# =====================================================

Write-Host "Checking project folder..."

$contextFile = "business_context.py"

if (Test-Path $contextFile) {
    Write-Host "business_context.py already exists. Skipping."
    exit
}

Write-Host "Creating business_context.py ..."

$pythonContent = @'
# =====================================================
# Business Context Intelligence Layer
# Safe add-on for AI Business Companion
# =====================================================

BUSINESS_PROFILES = {
    "Retail": {
        "currency": "INR",
        "kpis": ["Revenue", "Profit Margin", "Inventory Turnover"],
        "growth_suggestions": [
            "Introduce seasonal offers",
            "Optimize inventory using demand trends",
            "Increase digital payment incentives"
        ]
    },
    "Real Estate": {
        "currency": "INR",
        "kpis": ["Bookings", "Vacancy Rate", "ROI"],
        "growth_suggestions": [
            "Improve digital lead conversion",
            "Optimize pricing by locality",
            "Focus on high-demand zones"
        ]
    },
    "Manufacturing": {
        "currency": "INR",
        "kpis": ["Production Cost", "Downtime", "Yield"],
        "growth_suggestions": [
            "Reduce machine idle time",
            "Optimize raw material sourcing",
            "Improve quality control"
        ]
    },
    "General Business": {
        "currency": "INR",
        "kpis": ["Revenue", "Expenses", "Profit"],
        "growth_suggestions": [
            "Track monthly revenue consistently",
            "Adopt digital billing",
            "Improve customer retention"
        ]
    }
}


def analyze_data_quality(record_count):
    if record_count < 5:
        return {
            "warning": "Limited data available. Insights may not be conclusive.",
            "recommendation": [
                "Increase data collection frequency",
                "Maintain consistent financial records",
                "Track KPIs regularly"
            ]
        }
    return None


def get_business_context(business_type):
    return BUSINESS_PROFILES.get(business_type, BUSINESS_PROFILES["General Business"])
'@

Set-Content -Path $contextFile -Value $pythonContent -Encoding UTF8

Write-Host "business_context.py created successfully."
Write-Host "No existing files were modified."

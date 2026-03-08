#!/usr/bin/env python3
"""
Build time-series trend data from archive snapshots and current listings.
Generates trends.json with monthly average PSF for sale/rent per property.
"""
import os
import sys
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, DASHBOARD_PUBLIC_DIR, ALL_PROPERTIES


def parse_listed_date(listed_str, scraped_at):
    """Convert relative dates like '25 days ago' to approximate date."""
    if not listed_str or not scraped_at:
        return None
    try:
        base = datetime.fromisoformat(scraped_at.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None

    listed_str = listed_str.lower().strip()

    # Match patterns like "25 days ago", "3 hours ago", "1 month ago"
    m = re.match(r"(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", listed_str)
    if m:
        num = int(m.group(1))
        unit = m.group(2)
        if unit == "minute":
            return base - timedelta(minutes=num)
        elif unit == "hour":
            return base - timedelta(hours=num)
        elif unit == "day":
            return base - timedelta(days=num)
        elif unit == "week":
            return base - timedelta(weeks=num)
        elif unit == "month":
            return base - timedelta(days=num * 30)
        elif unit == "year":
            return base - timedelta(days=num * 365)

    # "just now", "today"
    if "just now" in listed_str or "today" in listed_str:
        return base

    return None


def load_archive_snapshots():
    """Load all daily archive files."""
    archive_dir = os.path.join(DATA_DIR, "archive")
    snapshots = []
    if not os.path.exists(archive_dir):
        return snapshots
    for fname in sorted(os.listdir(archive_dir)):
        if fname.startswith("scrape_") and fname.endswith(".json"):
            date_str = fname.replace("scrape_", "").replace(".json", "")
            fpath = os.path.join(archive_dir, fname)
            try:
                with open(fpath) as f:
                    data = json.load(f)
                snapshots.append({"date": date_str, "data": data})
            except Exception as e:
                print(f"  Warning: Could not load {fname}: {e}")
    return snapshots


def load_current_listings():
    """Load current consolidated listing files."""
    result = {"sale": [], "rent": [], "transactions": []}
    for key, fname in [("sale", "sale_listings.json"), ("rent", "rent_listings.json"),
                        ("transactions", "transactions.json")]:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                result[key] = json.load(f)
    return result


def get_month_key(dt):
    """Return YYYY-MM string from a datetime."""
    return dt.strftime("%Y-%m")


def build_trends():
    """Build monthly trend data from all available sources."""
    print("  Building trend data...")

    # Collect all listings with timestamps
    all_sale = []
    all_rent = []

    # 1. Load from archive snapshots
    snapshots = load_archive_snapshots()
    print(f"  Found {len(snapshots)} archive snapshots")
    for snap in snapshots:
        for item in snap["data"].get("sale", []):
            all_sale.append(item)
        for item in snap["data"].get("rent", []):
            all_rent.append(item)

    # 2. Load current listings (may overlap with archive but we dedupe by URL)
    current = load_current_listings()
    for item in current["sale"]:
        all_sale.append(item)
    for item in current["rent"]:
        all_rent.append(item)

    # Deduplicate by URL
    def dedupe(items):
        seen = set()
        unique = []
        for item in items:
            key = item.get("url") or f"{item.get('title','')}|{item.get('price','')}|{item.get('scraped_at','')}"
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    all_sale = dedupe(all_sale)
    all_rent = dedupe(all_rent)
    print(f"  Total unique: {len(all_sale)} sale, {len(all_rent)} rent listings")

    # 3. Assign each listing a "data month" based on listed_date or scraped_at
    property_names = [p["name"] for p in ALL_PROPERTIES]

    # monthly_data[property][month] = { sale_psf: [values], rent_psf: [values],
    #                                   sale_prices: [values], rent_prices: [values] }
    monthly_data = defaultdict(lambda: defaultdict(lambda: {
        "sale_psf": [], "rent_psf": [],
        "sale_prices": [], "rent_prices": [],
    }))

    def assign_month(item):
        """Determine which month a listing belongs to."""
        # Try listed_date first (gives us better historical spread)
        listed = item.get("listed_date")
        scraped = item.get("scraped_at")
        dt = parse_listed_date(listed, scraped)
        if dt:
            return get_month_key(dt)
        # Fall back to scraped_at
        if scraped:
            try:
                return get_month_key(datetime.fromisoformat(scraped.split("+")[0]))
            except Exception:
                pass
        return None

    # Process sale listings
    for item in all_sale:
        prop = item.get("property")
        if not prop or prop not in property_names:
            continue
        month = assign_month(item)
        if not month:
            continue
        if item.get("price_psf"):
            monthly_data[prop][month]["sale_psf"].append(item["price_psf"])
        if item.get("price"):
            monthly_data[prop][month]["sale_prices"].append(item["price"])

    # Process rent listings (with same filters as dashboard)
    for item in all_rent:
        prop = item.get("property")
        if not prop or prop not in property_names:
            continue
        month = assign_month(item)
        if not month:
            continue
        price = item.get("price", 0)
        psf = item.get("price_psf", 0)
        if price and price < 20000:
            monthly_data[prop][month]["rent_prices"].append(price)
        if psf and psf < 10:
            monthly_data[prop][month]["rent_psf"].append(psf)

    # 4. Also try to extract historical transaction data with dates
    # EdgeProp insights may have transaction dates
    details_path = os.path.join(DATA_DIR, "property_details.json")
    if os.path.exists(details_path):
        with open(details_path) as f:
            details = json.load(f)
        for detail in details:
            prop = detail.get("property")
            if not prop or prop not in property_names:
                continue
            for txn in detail.get("transactions", []):
                date_str = txn.get("date", "")
                psf = txn.get("price_psf")
                if date_str and psf:
                    # Try to parse date like "Jan 2024", "2024-01", etc.
                    dt = None
                    for fmt in ["%b %Y", "%B %Y", "%Y-%m", "%d %b %Y", "%Y-%m-%d"]:
                        try:
                            dt = datetime.strptime(date_str.strip(), fmt)
                            break
                        except ValueError:
                            continue
                    if dt:
                        month = get_month_key(dt)
                        monthly_data[prop][month]["sale_psf"].append(psf)

    # 5. Compute monthly averages and build output
    trends = {
        "generated_at": datetime.now().isoformat(),
        "properties": {},
        "summary": {},
    }

    all_months = set()
    for prop in monthly_data:
        for month in monthly_data[prop]:
            all_months.add(month)

    all_months = sorted(all_months)

    for prop_name in property_names:
        prop_config = next((p for p in ALL_PROPERTIES if p["name"] == prop_name), {})
        prop_trends = {
            "region": prop_config.get("region", ""),
            "is_target": prop_config.get("is_target", False),
            "monthly": [],
        }

        for month in all_months:
            data = monthly_data.get(prop_name, {}).get(month, {})
            entry = {"month": month}

            sale_psf = data.get("sale_psf", [])
            if sale_psf:
                sale_psf.sort()
                entry["sale_psf_avg"] = round(sum(sale_psf) / len(sale_psf), 2)
                entry["sale_psf_median"] = round(sale_psf[len(sale_psf) // 2], 2)
                entry["sale_psf_min"] = round(min(sale_psf), 2)
                entry["sale_psf_max"] = round(max(sale_psf), 2)
                entry["sale_count"] = len(sale_psf)

            rent_psf = data.get("rent_psf", [])
            if rent_psf:
                rent_psf.sort()
                entry["rent_psf_avg"] = round(sum(rent_psf) / len(rent_psf), 2)
                entry["rent_psf_median"] = round(rent_psf[len(rent_psf) // 2], 2)
                entry["rent_count"] = len(rent_psf)

            sale_prices = data.get("sale_prices", [])
            if sale_prices:
                sale_prices.sort()
                entry["sale_price_avg"] = round(sum(sale_prices) / len(sale_prices), 2)
                entry["sale_price_median"] = sale_prices[len(sale_prices) // 2]

            rent_prices = data.get("rent_prices", [])
            if rent_prices:
                rent_prices.sort()
                entry["rent_price_avg"] = round(sum(rent_prices) / len(rent_prices), 2)
                entry["rent_price_median"] = rent_prices[len(rent_prices) // 2]

            # Only include months that have at least some data
            if len(entry) > 1:
                prop_trends["monthly"].append(entry)

        trends["properties"][prop_name] = prop_trends

    # 6. Build region-level summary trends
    regions = set(p["region"] for p in ALL_PROPERTIES)
    for region in regions:
        region_months = defaultdict(lambda: {"sale_psf": [], "rent_psf": []})
        for prop in ALL_PROPERTIES:
            if prop["region"] != region:
                continue
            for month_data in trends["properties"].get(prop["name"], {}).get("monthly", []):
                m = month_data["month"]
                if "sale_psf_avg" in month_data:
                    region_months[m]["sale_psf"].append(month_data["sale_psf_avg"])
                if "rent_psf_avg" in month_data:
                    region_months[m]["rent_psf"].append(month_data["rent_psf_avg"])

        region_trend = []
        for month in sorted(region_months.keys()):
            entry = {"month": month}
            sp = region_months[month]["sale_psf"]
            rp = region_months[month]["rent_psf"]
            if sp:
                entry["sale_psf_avg"] = round(sum(sp) / len(sp), 2)
            if rp:
                entry["rent_psf_avg"] = round(sum(rp) / len(rp), 2)
            if len(entry) > 1:
                region_trend.append(entry)

        trends["summary"][region] = {"monthly": region_trend}

    # 7. Save
    for directory in [DATA_DIR, DASHBOARD_PUBLIC_DIR]:
        filepath = os.path.join(directory, "trends.json")
        with open(filepath, "w") as f:
            json.dump(trends, f, indent=2, default=str)
        print(f"  Saved {filepath}")

    # Stats
    total_months = len(all_months)
    props_with_data = sum(1 for p in trends["properties"].values() if p.get("monthly"))
    print(f"  Trends: {total_months} months, {props_with_data} properties with data")

    return trends


if __name__ == "__main__":
    print("=== Building Trend Data ===")
    build_trends()
    print("=== Done ===")

#!/usr/bin/env python3
"""
Main scraper orchestrator for the Klang Valley Property Analysis dashboard.
Runs all source scrapers and consolidates data into JSON files.
"""
import os
import sys
import json
from datetime import datetime

# Add scraper directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, DASHBOARD_PUBLIC_DIR, ALL_PROPERTIES, PRICE_TIERS, AMENITY_TYPES
from sources import propertyguru, edgeprop, iproperty, brickz, napic


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(DASHBOARD_PUBLIC_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "archive"), exist_ok=True)


def load_existing(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return []


def save_data(filename, data):
    for directory in [DATA_DIR, DASHBOARD_PUBLIC_DIR]:
        filepath = os.path.join(directory, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  Saved {filepath}")


def merge_listings(existing, new_items):
    keys = set()
    for item in existing:
        key = item.get("url") or f"{item.get('title', '')}|{item.get('price', '')}|{item.get('source', '')}"
        keys.add(key)

    merged = list(existing)
    added = 0
    for item in new_items:
        key = item.get("url") or f"{item.get('title', '')}|{item.get('price', '')}|{item.get('source', '')}"
        if key not in keys:
            merged.append(item)
            keys.add(key)
            added += 1

    print(f"  Merged: {added} new, {len(merged)} total")
    return merged


def compute_stats(sale_listings, rent_listings, transactions):
    stats = {}

    sale_prices = [l["price"] for l in sale_listings if l.get("price")]
    if sale_prices:
        sale_prices.sort()
        stats["sale_price_min"] = min(sale_prices)
        stats["sale_price_max"] = max(sale_prices)
        stats["sale_price_median"] = sale_prices[len(sale_prices) // 2]
        stats["sale_price_avg"] = round(sum(sale_prices) / len(sale_prices), 2)
        stats["total_sale_listings"] = len(sale_prices)

    sale_psf = [l["price_psf"] for l in sale_listings if l.get("price_psf")]
    if sale_psf:
        sale_psf.sort()
        stats["sale_psf_min"] = min(sale_psf)
        stats["sale_psf_max"] = max(sale_psf)
        stats["sale_psf_median"] = sale_psf[len(sale_psf) // 2]
        stats["sale_psf_avg"] = round(sum(sale_psf) / len(sale_psf), 2)

    # Filter rentals: real rent is typically < RM 20,000/month; anything higher is likely a misclassified sale
    rent_prices = [l["price"] for l in rent_listings if l.get("price") and l["price"] < 20000]
    if rent_prices:
        rent_prices.sort()
        stats["rent_price_min"] = min(rent_prices)
        stats["rent_price_max"] = max(rent_prices)
        stats["rent_price_median"] = rent_prices[len(rent_prices) // 2]
        stats["rent_price_avg"] = round(sum(rent_prices) / len(rent_prices), 2)
        stats["total_rent_listings"] = len(rent_prices)

    # Rental PSF (filter: real rental PSF is typically < RM 10/sqft)
    rent_psf = [l["price_psf"] for l in rent_listings if l.get("price_psf") and l["price_psf"] < 10]
    if rent_psf:
        rent_psf.sort()
        stats["rent_psf_min"] = min(rent_psf)
        stats["rent_psf_max"] = max(rent_psf)
        stats["rent_psf_median"] = round(rent_psf[len(rent_psf) // 2], 2)
        stats["rent_psf_avg"] = round(sum(rent_psf) / len(rent_psf), 2)

    if stats.get("sale_price_median") and stats.get("rent_price_median"):
        annual = stats["rent_price_median"] * 12
        stats["estimated_yield"] = round((annual / stats["sale_price_median"]) * 100, 2)

    txn_prices = [t["price"] for t in transactions if t.get("price") and t.get("type") != "area_summary"]
    if txn_prices:
        txn_prices.sort()
        stats["txn_price_min"] = min(txn_prices)
        stats["txn_price_max"] = max(txn_prices)
        stats["txn_price_median"] = txn_prices[len(txn_prices) // 2]
        stats["total_transactions"] = len(txn_prices)

    txn_psf = [t["price_psf"] for t in transactions if t.get("price_psf") and t.get("type") != "area_summary"]
    if txn_psf:
        txn_psf.sort()
        stats["txn_psf_median"] = txn_psf[len(txn_psf) // 2]
        stats["txn_psf_avg"] = round(sum(txn_psf) / len(txn_psf), 2)

    return stats


def build_dashboard(sale, rent, transactions, market_data, news, details):
    dashboard = {
        "last_updated": datetime.now().isoformat(),
        "properties": {},
        "regions": {},
        "price_tiers": PRICE_TIERS,
        "amenity_types": AMENITY_TYPES,
        "market_overview": market_data,
        "news": news[:20],
        "property_details": details,
    }

    for prop in ALL_PROPERTIES:
        name = prop["name"]
        prop_sale = [l for l in sale if l.get("property") == name]
        prop_rent = [l for l in rent if l.get("property") == name]
        prop_txns = [t for t in transactions if t.get("property") == name]

        dashboard["properties"][name] = {
            "info": {
                "developer": prop.get("developer", ""),
                "region": prop["region"],
                "area": prop["area"],
                "tenure": prop.get("tenure", ""),
                "property_type": prop.get("property_type", ""),
                "total_units": prop.get("total_units"),
                "completion": prop.get("completion", ""),
                "is_target": prop.get("is_target", False),
                "price_tier": prop.get("price_tier", "mid"),
                "amenities": prop.get("amenities", {}),
            },
            "sale_listings": prop_sale,
            "rent_listings": prop_rent,
            "transactions": prop_txns,
            "stats": compute_stats(prop_sale, prop_rent, prop_txns),
        }

    regions = set(p["region"] for p in ALL_PROPERTIES)
    for region in regions:
        r_sale = [l for l in sale if l.get("region") == region]
        r_rent = [l for l in rent if l.get("region") == region]
        r_txns = [t for t in transactions if region.lower() in (t.get("region", "")).lower()]
        region_props = [p["name"] for p in ALL_PROPERTIES if p["region"] == region]

        dashboard["regions"][region] = {
            "properties": region_props,
            "total_sale_listings": len(r_sale),
            "total_rent_listings": len(r_rent),
            "total_transactions": len([t for t in r_txns if t.get("type") != "area_summary"]),
            "stats": compute_stats(r_sale, r_rent, r_txns),
        }

    return dashboard


def run():
    print(f"\n{'='*60}")
    print(f"  Property Analysis Scraper - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    ensure_dirs()

    results = {
        "sale": [], "rent": [], "transactions": [],
        "market": [], "news": [], "details": [], "errors": [],
    }

    def safe(name, fn, key):
        try:
            data = fn()
            results[key].extend(data)
            print(f"  -> {len(data)} items")
        except Exception as e:
            print(f"  ERROR [{name}]: {e}")
            results["errors"].append({"source": name, "error": str(e)})

    # EdgeProp (works well with curl_cffi)
    print("\n--- EdgeProp ---")
    safe("edgeprop_sale", lambda: edgeprop.scrape_listings("sale"), "sale")
    safe("edgeprop_rent", lambda: edgeprop.scrape_listings("rent"), "rent")
    safe("edgeprop_insights", edgeprop.scrape_area_insights, "details")
    safe("edgeprop_news", edgeprop.scrape_news, "news")

    # iProperty
    print("\n--- iProperty ---")
    safe("iproperty_sale", lambda: iproperty.scrape_listings("sale"), "sale")
    safe("iproperty_rent", lambda: iproperty.scrape_listings("rent"), "rent")

    # PropertyGuru (may be blocked by Cloudflare)
    print("\n--- PropertyGuru ---")
    safe("pg_sale", lambda: propertyguru.scrape_listings("sale"), "sale")
    safe("pg_rent", lambda: propertyguru.scrape_listings("rent"), "rent")
    safe("pg_details", propertyguru.scrape_property_details, "details")

    # Brickz.my (transaction data)
    print("\n--- Brickz.my ---")
    safe("brickz_txns", brickz.scrape_transactions, "transactions")
    safe("brickz_summary", brickz.scrape_area_summary, "market")

    # NAPIC
    print("\n--- NAPIC ---")
    safe("napic_sales", napic.scrape_open_sales_data, "market")
    safe("napic_snapshots", napic.scrape_market_snapshot, "market")
    safe("napic_txns", napic.scrape_transaction_data, "market")

    # Save results
    print(f"\n--- Saving ---")
    merged_sale = merge_listings(load_existing("sale_listings.json"), results["sale"])
    merged_rent = merge_listings(load_existing("rent_listings.json"), results["rent"])
    merged_txns = merge_listings(load_existing("transactions.json"), results["transactions"])

    save_data("sale_listings.json", merged_sale)
    save_data("rent_listings.json", merged_rent)
    save_data("transactions.json", merged_txns)
    save_data("market_data.json", results["market"])
    save_data("news.json", results["news"])
    save_data("property_details.json", results["details"])

    dashboard = build_dashboard(
        merged_sale, merged_rent, merged_txns,
        results["market"], results["news"], results["details"]
    )
    save_data("dashboard.json", dashboard)

    # Build trends (time-series data)
    print(f"\n--- Building Trends ---")
    try:
        from build_trends import build_trends
        build_trends()
    except Exception as e:
        print(f"  ERROR [trends]: {e}")
        results["errors"].append({"source": "trends", "error": str(e)})

    # Archive
    today = datetime.now().strftime("%Y-%m-%d")
    archive_file = os.path.join(DATA_DIR, "archive", f"scrape_{today}.json")
    with open(archive_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "sale": len(results["sale"]),
        "rent": len(results["rent"]),
        "transactions": len(results["transactions"]),
        "market": len(results["market"]),
        "news": len(results["news"]),
        "errors": len(results["errors"]),
    }
    log_file = os.path.join(DATA_DIR, "scrape_log.json")
    logs = []
    if os.path.exists(log_file):
        with open(log_file) as f:
            logs = json.load(f)
    logs.append(log_entry)
    with open(log_file, "w") as f:
        json.dump(logs[-90:], f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Done! Sale: {len(merged_sale)} | Rent: {len(merged_rent)} | Txns: {len(merged_txns)}")
    print(f"  Market: {len(results['market'])} | News: {len(results['news'])} | Errors: {len(results['errors'])}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()

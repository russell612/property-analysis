"""
Brickz.my scraper using curl_cffi.
Provides subsale transaction records from JPPH.
"""
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from config import PROPERTIES, REGIONS, RATE_LIMIT_DELAY


def _get(url):
    resp = cffi_requests.get(url, impersonate="chrome", timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_transactions():
    """Scrape area-level transaction data from Brickz.my."""
    all_transactions = []

    for region in REGIONS:
        path = region["brickz_path"]
        url = f"https://www.brickz.my/transactions/residential/{path}/"
        print(f"  [Brickz] Scraping transactions for {region['name']}...")

        try:
            html = _get(url)
            txns = _parse_transaction_page(html, region)
            all_transactions.extend(txns)
            print(f"  Found {len(txns)} entries")
        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return all_transactions


def _parse_transaction_page(html, region):
    """Parse Brickz.my transaction page."""
    soup = BeautifulSoup(html, "lxml")
    transactions = []

    # Parse tables
    tables = soup.select("table")
    for table in tables:
        rows = table.select("tr")
        if not rows:
            continue

        headers = [th.get_text(strip=True).lower() for th in rows[0].select("th, td")]
        is_txn = any(k in " ".join(headers) for k in ["price", "psf", "date", "size"])

        if not is_txn:
            continue

        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.select("td")]
            if len(cells) < 2:
                continue

            txn = {
                "region": region["name"],
                "source": "brickz",
                "scraped_at": datetime.now().isoformat(),
            }

            for i, header in enumerate(headers):
                if i >= len(cells):
                    break
                val = cells[i]

                if "project" in header or "name" in header or "property" in header:
                    # Clean up concatenated property names
                    txn["property"] = _clean_property_name(val)
                elif "price" in header and "psf" not in header and "per" not in header:
                    txn["price"] = _parse_number(val)
                    txn["price_text"] = val
                elif "psf" in header or "per sq" in header:
                    txn["price_psf"] = _parse_number(val)
                elif "size" in header or "area" in header:
                    txn["size_sqft"] = _parse_number(val)
                elif "date" in header:
                    txn["date"] = val
                elif "type" in header:
                    txn["unit_type"] = _clean_property_type(val)
                elif "tenure" in header:
                    txn["tenure"] = val

            if txn.get("price") or txn.get("price_psf"):
                transactions.append(txn)

    # Extract summary stats
    text = soup.get_text(" ", strip=True)
    summary = _extract_summary(text, region)
    if summary:
        transactions.append(summary)

    return transactions


def _extract_summary(text, region):
    """Extract area summary statistics from page text."""
    summary = {
        "region": region["name"],
        "source": "brickz",
        "type": "area_summary",
        "scraped_at": datetime.now().isoformat(),
    }

    patterns = {
        "median_price": r"median\s*(?:property\s*)?price\s*:?\s*RM\s*([\d,]+)",
        "median_psf": r"median\s*(?:price\s*)?(?:per\s*sq\.?\s*ft\.?|psf)\s*:?\s*RM\s*([\d,]+)",
        "total_transactions": r"(\d+)\s*(?:residential\s*)?(?:property\s*)?transactions?",
        "total_projects": r"(\d+)\s*projects?",
    }

    found = False
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).replace(",", "")
            summary[key] = int(val) if val.isdigit() else float(val)
            found = True

    return summary if found else None


def scrape_area_summary():
    """Scrape area summaries from Brickz.my."""
    summaries = []

    for region in REGIONS:
        path = region["brickz_path"]
        url = f"https://www.brickz.my/transactions/residential/{path}/"
        print(f"  [Brickz] Area summary for {region['name']}...")

        try:
            html = _get(url)
            text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
            summary = _extract_summary(text, region)
            if summary:
                summaries.append(summary)
        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return summaries


def _clean_property_name(text):
    """Clean concatenated property names from Brickz."""
    # Brickz concatenates: "PROPERTY NAMEAREA,CITYTYPE"
    # Try to split on known area names
    for area in ["SEGAMBUT", "OLD KLANG ROAD", "KUALA LUMPUR"]:
        idx = text.upper().find(area)
        if idx > 0:
            return text[:idx].strip()
    return text.strip()


def _clean_property_type(text):
    """Clean concatenated property type strings."""
    text = text.strip()
    if text.startswith("FREEHOLD") or text.startswith("LEASEHOLD"):
        tenure_end = text.find("HOLD") + 4
        return text[tenure_end:].strip() if tenure_end < len(text) else text
    return text


def _parse_number(text):
    if not text:
        return None
    cleaned = text.replace(",", "").replace("RM", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        match = re.search(r"([\d.]+)", cleaned)
        return float(match.group(1)) if match else None

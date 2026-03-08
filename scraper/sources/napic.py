"""
NAPIC (National Property Information Centre) scraper using curl_cffi.
"""
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from config import REGIONS, RATE_LIMIT_DELAY


def _get(url):
    resp = cffi_requests.get(url, impersonate="chrome", timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_open_sales_data():
    """Scrape NAPIC open sales data."""
    data = []
    urls = [
        "https://napic.jpph.gov.my/en/open-sales-data",
        "https://napic2.jpph.gov.my/en/open-sales-data",
    ]

    for url in urls:
        print(f"  [NAPIC] Trying: {url}")
        try:
            html = _get(url)
            entries = _parse_open_sales(html)
            if entries:
                data.extend(entries)
                print(f"  Found {len(entries)} entries")
                break
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(RATE_LIMIT_DELAY)

    return data


def _parse_open_sales(html):
    """Parse NAPIC open sales page."""
    soup = BeautifulSoup(html, "lxml")
    entries = []

    # Look for download links
    for link in soup.select("a[href]"):
        href = link.get("href", "")
        text = link.get_text(strip=True)
        if any(ext in href.lower() for ext in [".xlsx", ".xls", ".csv", ".pdf"]):
            entries.append({
                "text": text,
                "url": href if href.startswith("http") else f"https://napic.jpph.gov.my{href}",
                "type": "download_link",
                "source": "napic",
                "scraped_at": datetime.now().isoformat(),
            })

    # Parse tables
    for table in soup.select("table"):
        rows = table.select("tr")
        if not rows:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].select("th, td")]

        for row in rows[1:]:
            cells = [td.get_text(strip=True) for td in row.select("td")]
            if len(cells) < 2:
                continue

            entry = {
                "source": "napic",
                "scraped_at": datetime.now().isoformat(),
            }

            for i, header in enumerate(headers):
                if i >= len(cells):
                    break
                val = cells[i]
                if any(k in header for k in ["state", "negeri"]):
                    entry["state"] = val
                elif any(k in header for k in ["district", "daerah"]):
                    entry["district"] = val
                elif any(k in header for k in ["scheme", "project", "nama"]):
                    entry["project_name"] = val
                elif any(k in header for k in ["price", "harga"]):
                    entry["price"] = _parse_price(val)

            # Only keep KL entries
            if entry.get("state") and "kuala lumpur" not in entry.get("state", "").lower():
                continue

            entries.append(entry)

    return entries


def scrape_market_snapshot():
    """Scrape NAPIC market data and publication links."""
    snapshots = []

    for url in [
        "https://napic.jpph.gov.my/en/data-visualization",
        "https://napic.jpph.gov.my/en/archives",
    ]:
        print(f"  [NAPIC] Fetching: {url}")
        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)

            # Extract market overview data
            data = {
                "source": "napic",
                "type": "market_overview",
                "url": url,
                "scraped_at": datetime.now().isoformat(),
            }

            patterns = {
                "total_transactions_volume": r"(?:volume|bilangan)\s*(?:of\s*)?transactions?\s*:?\s*([\d,]+)",
                "quarter": r"(Q[1-4]\s*20\d{2})",
                "house_price_index": r"(?:MHPI|house\s*price\s*index)\s*:?\s*([\d.]+)",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).replace(",", "")
                    data[key] = val

            # Find publication links
            for link in soup.select("a[href]"):
                link_text = link.get_text(strip=True).lower()
                href = link.get("href", "")
                if any(k in link_text for k in ["snapshot", "property market", "laporan"]):
                    snapshots.append({
                        "title": link.get_text(strip=True),
                        "url": href if href.startswith("http") else f"https://napic.jpph.gov.my{href}",
                        "type": "publication",
                        "source": "napic",
                        "scraped_at": datetime.now().isoformat(),
                    })

            if len(data) > 4:
                snapshots.append(data)

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return snapshots


def scrape_transaction_data():
    """Scrape NAPIC transaction archive links."""
    data = []

    for url in [
        "https://napic.jpph.gov.my/en/archives/jadual-data-transaksi-harta-tanah",
        "https://napic2.jpph.gov.my/en/archives/jadual-data-transaksi-harta-tanah",
    ]:
        print(f"  [NAPIC] Transaction archives: {url}")
        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")

            for link in soup.select("a[href]"):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if any(ext in href.lower() for ext in [".xlsx", ".xls", ".csv", ".pdf"]):
                    if any(k in text.lower() for k in ["kuala lumpur", "kl", "national", "residential"]):
                        data.append({
                            "title": text,
                            "url": href if href.startswith("http") else f"https://napic.jpph.gov.my{href}",
                            "type": "transaction_data_file",
                            "source": "napic",
                            "scraped_at": datetime.now().isoformat(),
                        })

            if data:
                break

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return data


def _parse_price(text):
    if not text:
        return None
    cleaned = text.replace(",", "")
    match = re.search(r"RM\s*([\d.]+)", cleaned)
    if match:
        return float(match.group(1))
    match = re.search(r"([\d.]+)", cleaned)
    return float(match.group(1)) if match else None

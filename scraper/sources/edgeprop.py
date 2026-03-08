"""
EdgeProp.my scraper using curl_cffi to bypass Cloudflare.
Scrapes property listings, insights, and news.
"""
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from config import ALL_PROPERTIES, REGIONS, RATE_LIMIT_DELAY
import time


def _get(url):
    """Make a GET request using curl_cffi with Chrome impersonation."""
    resp = cffi_requests.get(url, impersonate="chrome", timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_listings(listing_type="sale"):
    """Scrape EdgeProp sale/rental listings for target properties."""
    all_listings = []

    for prop in ALL_PROPERTIES:
        slug = prop.get("edgeprop_slug")
        listing_id = prop.get("edgeprop_listing_id") or prop.get("edgeprop_id")
        if not slug or not listing_id:
            continue

        # Use the correct EdgeProp area path (kl-city for Bamboo Hills)
        area = prop.get("edgeprop_area", prop["area"].lower().replace(" ", "-"))
        if listing_type == "sale":
            url = f"https://www.edgeprop.my/buy/kuala-lumpur/{area}/{slug}/all-residential/{listing_id}"
        else:
            url = f"https://www.edgeprop.my/rent/kuala-lumpur/{area}/{slug}/all-residential/{listing_id}"

        tag = "[Target]" if prop.get("is_target") else "[Comp]"
        print(f"  [EdgeProp] {tag} Scraping {listing_type} for {prop['name']}...")

        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")

            # EdgeProp listing cards are <a> tags linking to /listing/
            cards = soup.select('a[href*="/listing/"]')
            print(f"  Found {len(cards)} listing cards")

            for card in cards:
                listing = _parse_card(card, prop, listing_type, url)
                if listing:
                    listing["is_target"] = prop.get("is_target", False)
                    listing["price_tier"] = prop.get("price_tier", "mid")
                    all_listings.append(listing)

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    # Also try the search-based URL with label for properties that have edgeprop_id
    for prop in ALL_PROPERTIES:
        slug = prop.get("edgeprop_slug")
        ep_id = prop.get("edgeprop_id")
        if not slug or not ep_id:
            continue

        search_url = f"https://www.edgeprop.my/buy/kuala-lumpur/kl-city/{slug}/all-residential/{ep_id}?searchedLabel={prop['name'].replace(' ', '+')}"
        try:
            html = _get(search_url)
            soup = BeautifulSoup(html, "lxml")
            cards = soup.select('a[href*="/listing/"]')
            for card in cards:
                listing = _parse_card(card, prop, listing_type, search_url)
                if listing and not any(
                    l.get("url") == listing.get("url") for l in all_listings
                ):
                    listing["is_target"] = prop.get("is_target", False)
                    listing["price_tier"] = prop.get("price_tier", "mid")
                    all_listings.append(listing)
        except Exception:
            pass

        time.sleep(RATE_LIMIT_DELAY)

    return all_listings


def _parse_card(card, prop, listing_type, source_url):
    """Parse a single EdgeProp listing card."""
    text = card.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    listing = {
        "property": prop["name"],
        "region": prop["region"],
        "area": prop["area"],
        "type": listing_type,
        "source": "edgeprop",
        "scraped_at": datetime.now().isoformat(),
    }

    # URL
    href = card.get("href", "")
    if href:
        if not href.startswith("http"):
            href = f"https://www.edgeprop.my{href}"
        listing["url"] = href

    # Title - usually the 2nd line (after a number)
    for line in lines[:5]:
        if (
            len(line) > 5
            and not line.startswith("RM")
            and not re.match(r"^\d+$", line)
            and "Add to" not in line
        ):
            listing["title"] = line
            break

    # Price - find "RM" followed by number on next line or same line
    for i, line in enumerate(lines):
        if line == "RM" and i + 1 < len(lines):
            price_text = lines[i + 1]
            listing["price_text"] = f"RM {price_text}"
            listing["price"] = _parse_number_from_text(price_text)
            break
        elif line.startswith("RM "):
            listing["price_text"] = line
            listing["price"] = _parse_price(line)
            break

    # PSF
    psf_match = re.search(r"\(RM\s*([\d,.]+)\s*Psf\)", text, re.IGNORECASE)
    if psf_match:
        listing["price_psf"] = float(psf_match.group(1).replace(",", ""))

    # Beds/Baths/Size
    for i, line in enumerate(lines):
        if "Bed" in line and i > 0:
            bed_val = re.search(r"(\d+)", lines[i - 1])
            if bed_val:
                listing["bedrooms"] = int(bed_val.group(1))
        if "Bath" in line and i > 0:
            bath_val = re.search(r"(\d+)", lines[i - 1])
            if bath_val:
                listing["bathrooms"] = int(bath_val.group(1))

    # Size
    size_match = re.search(r"(\d[\d,]*)\s*sqft", text, re.IGNORECASE)
    if size_match:
        listing["size_sqft"] = float(size_match.group(1).replace(",", ""))

    # Listed date
    listed_match = re.search(r"Listed\s*(.+?)(?:\s*by|$)", text)
    if listed_match:
        listing["listed_date"] = listed_match.group(1).strip()

    # Compute PSF if not found but have price and size
    if not listing.get("price_psf") and listing.get("price") and listing.get("size_sqft"):
        listing["price_psf"] = round(listing["price"] / listing["size_sqft"], 2)

    # Only return if we have meaningful data
    if listing.get("price") or listing.get("title"):
        return listing
    return None


def scrape_area_insights():
    """Scrape EdgeProp condo insights pages."""
    insights = []

    for prop in ALL_PROPERTIES:
        slug = prop.get("edgeprop_slug")
        ep_id = prop.get("edgeprop_id")
        if not slug or not ep_id:
            continue

        url = f"https://www.edgeprop.my/condo/{slug}-{ep_id}"
        print(f"  [EdgeProp] Fetching insights for {prop['name']}...")

        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)

            insight = {
                "property": prop["name"],
                "region": prop["region"],
                "source": "edgeprop",
                "url": url,
                "scraped_at": datetime.now().isoformat(),
                "transactions": [],
            }

            # Parse transaction tables
            tables = soup.select("table")
            for table in tables:
                rows = table.select("tr")
                if not rows:
                    continue
                headers = [th.get_text(strip=True).lower() for th in rows[0].select("th, td")]
                if any("price" in h or "date" in h for h in headers):
                    for row in rows[1:]:
                        cells = [td.get_text(strip=True) for td in row.select("td")]
                        if len(cells) >= 2:
                            txn = {"raw": cells}
                            for j, header in enumerate(headers):
                                if j < len(cells):
                                    if "price" in header and "psf" not in header:
                                        txn["price"] = _parse_price(cells[j])
                                    elif "psf" in header:
                                        txn["price_psf"] = _parse_price(cells[j])
                                    elif "date" in header:
                                        txn["date"] = cells[j]
                                    elif "size" in header:
                                        txn["size_sqft"] = _parse_size(cells[j])
                            insight["transactions"].append(txn)

            # Key stats
            median_match = re.search(r"median\s*(?:price)?\s*(?:psf|per\s*sq)\s*:?\s*RM\s*([\d,]+)", text, re.IGNORECASE)
            if median_match:
                insight["median_psf"] = float(median_match.group(1).replace(",", ""))

            insights.append(insight)

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return insights


def scrape_news():
    """Scrape EdgeProp news articles related to target areas."""
    articles = []
    search_terms = ["bamboo hills residences", "old klang road property", "segambut property", "GenStarz"]

    for term in search_terms:
        url = f"https://www.edgeprop.my/content?q={term.replace(' ', '+')}"
        print(f"  [EdgeProp] Searching news for '{term}'...")

        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")

            for article_el in soup.select("article, [class*='article'], [class*='content-card'], .card"):
                title_el = article_el.select_one("h2, h3, [class*='title']")
                link_el = article_el.select_one("a[href]")
                date_el = article_el.select_one("[class*='date'], time, [class*='time']")

                if title_el:
                    art = {
                        "title": title_el.get_text(strip=True),
                        "source": "edgeprop",
                        "search_term": term,
                        "scraped_at": datetime.now().isoformat(),
                    }
                    if link_el:
                        href = link_el.get("href", "")
                        if href and not href.startswith("http"):
                            href = f"https://www.edgeprop.my{href}"
                        art["url"] = href
                    if date_el:
                        art["date"] = date_el.get_text(strip=True)
                    articles.append(art)

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    return articles


def _parse_price(text):
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"RM\s*([\d.]+)", text)
    if match:
        return float(match.group(1))
    return None


def _parse_number_from_text(text):
    if not text:
        return None
    cleaned = text.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_size(text):
    if not text:
        return None
    match = re.search(r"([\d,]+)\s*(?:sq\.?\s*ft|sqft)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


if __name__ == "__main__":
    print("=== EdgeProp Scraper ===")
    sale = scrape_listings("sale")
    print(f"Sale listings: {len(sale)}")
    for l in sale[:3]:
        print(f"  {l.get('title')} | RM {l.get('price')} | {l.get('size_sqft')} sqft")

    rent = scrape_listings("rent")
    print(f"Rent listings: {len(rent)}")

    insights = scrape_area_insights()
    print(f"Insights: {len(insights)}")

    news = scrape_news()
    print(f"News: {len(news)}")

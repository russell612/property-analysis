"""
PropertyGuru.com.my scraper.
Uses curl_cffi with Chrome impersonation to bypass Cloudflare,
and falls back to their search API if page scraping fails.
"""
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from config import ALL_PROPERTIES, RATE_LIMIT_DELAY


def _get(url, retries=3):
    """GET request with curl_cffi Chrome impersonation and retries."""
    for attempt in range(retries):
        try:
            resp = cffi_requests.get(
                url,
                impersonate="chrome",
                timeout=30,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                },
            )
            if resp.status_code == 200 and "Just a moment" not in resp.text[:500]:
                return resp.text
            elif resp.status_code == 403:
                print(f"    Cloudflare block (attempt {attempt + 1}/{retries})")
                time.sleep(2 * (attempt + 1))
            else:
                return resp.text
        except Exception as e:
            print(f"    Request error (attempt {attempt + 1}): {e}")
            time.sleep(2)
    return None


def scrape_listings(listing_type="sale"):
    """Scrape PropertyGuru listings for target properties."""
    all_listings = []

    for prop in ALL_PROPERTIES:
        slug = prop["propertyguru_slug"]
        prop_id = prop["propertyguru_id"]
        if not slug or not prop_id:
            continue

        if listing_type == "sale":
            url = f"https://www.propertyguru.com.my/property-for-sale/at-{slug}-{prop_id}"
        else:
            url = f"https://www.propertyguru.com.my/property-for-rent/at-{slug}-{prop_id}"

        print(f"  [PropertyGuru] Scraping {listing_type} for {prop['name']}...")

        html = _get(url)
        if not html:
            print(f"  Could not fetch page (Cloudflare protected)")
            # Try the search API fallback
            listings = _scrape_via_search_api(prop, listing_type)
            all_listings.extend(listings)
            continue

        soup = BeautifulSoup(html, "lxml")

        # Check if we got actual content
        title = soup.title.get_text() if soup.title else ""
        if "Just a moment" in title:
            print(f"  Cloudflare challenge page detected, trying API fallback")
            listings = _scrape_via_search_api(prop, listing_type)
            all_listings.extend(listings)
            continue

        # Parse listing cards
        cards = soup.select(".listing-card-v2, .listing-card, [da-id*='listing-card']")
        print(f"  Found {len(cards)} listing cards")

        for card in cards:
            listing = _parse_card(card, prop, listing_type)
            if listing:
                all_listings.append(listing)

        # If no cards found, try to extract from JSON-LD or embedded data
        if not cards:
            listings = _extract_from_json(html, prop, listing_type)
            all_listings.extend(listings)

        time.sleep(RATE_LIMIT_DELAY)

    return all_listings


def _scrape_via_search_api(prop, listing_type):
    """Fallback: try PropertyGuru's internal search API."""
    listings = []

    # PropertyGuru has a search endpoint that returns JSON
    search_name = prop["name"].replace(" ", "+")
    listing_str = "sale" if listing_type == "sale" else "rent"
    api_url = f"https://www.propertyguru.com.my/property-for-{listing_str}?freetext={search_name}&market=residential&listing_type={listing_str}"

    html = _get(api_url)
    if not html:
        return listings

    soup = BeautifulSoup(html, "lxml")

    # Try JSON-LD
    listings = _extract_from_json(html, prop, listing_type)
    if listings:
        return listings

    # Try parsing listing cards
    cards = soup.select(".listing-card-v2, .listing-card")
    for card in cards:
        listing = _parse_card(card, prop, listing_type)
        if listing:
            listings.append(listing)

    return listings


def _parse_card(card, prop, listing_type):
    """Parse a PropertyGuru listing card."""
    text = card.get_text("\n", strip=True)

    listing = {
        "property": prop["name"],
        "region": prop["region"],
        "area": prop["area"],
        "type": listing_type,
        "source": "propertyguru",
        "scraped_at": datetime.now().isoformat(),
    }

    # Title
    title_el = card.select_one(".title-badge-wrapper h3, .title-location h3, h3")
    if title_el:
        listing["title"] = title_el.get_text(strip=True)

    # Price
    price_el = card.select_one(".listing-price")
    if price_el:
        listing["price_text"] = price_el.get_text(strip=True)
        listing["price"] = _parse_price(listing["price_text"])

    # PSF
    ppa_el = card.select_one(".listing-ppa")
    if ppa_el:
        ppa_text = ppa_el.get_text(strip=True)
        listing["price_psf"] = _parse_price(ppa_text)

    # Features (beds, baths, size)
    size_match = re.search(r"(\d[\d,]*)\s*sqft", text, re.IGNORECASE)
    if size_match:
        listing["size_sqft"] = float(size_match.group(1).replace(",", ""))

    feature_el = card.select_one(".listing-feature-group")
    if feature_el:
        feat_text = feature_el.get_text(" ", strip=True)
        nums = re.findall(r"(\d+)", feat_text)
        if len(nums) >= 1:
            listing["bedrooms"] = int(nums[0])
        if len(nums) >= 2:
            listing["bathrooms"] = int(nums[1])

    # Link
    link_el = card.select_one("a[href*='/property-listing/']") or card.select_one("a[href]")
    if link_el:
        href = link_el.get("href", "")
        if href and not href.startswith("http"):
            href = f"https://www.propertyguru.com.my{href}"
        listing["url"] = href

    # Compute PSF if missing
    if not listing.get("price_psf") and listing.get("price") and listing.get("size_sqft"):
        listing["price_psf"] = round(listing["price"] / listing["size_sqft"], 2)

    if listing.get("price") or listing.get("title"):
        return listing
    return None


def _extract_from_json(html, prop, listing_type):
    """Extract listings from JSON-LD or embedded script data."""
    listings = []
    soup = BeautifulSoup(html, "lxml")

    # Try JSON-LD structured data
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") == "ItemList":
                for item in data.get("itemListElement", []):
                    offer = item.get("item", {})
                    listing = {
                        "property": prop["name"],
                        "region": prop["region"],
                        "area": prop["area"],
                        "type": listing_type,
                        "source": "propertyguru",
                        "scraped_at": datetime.now().isoformat(),
                        "title": offer.get("name", ""),
                        "url": offer.get("url", ""),
                    }
                    if offer.get("offers", {}).get("price"):
                        listing["price"] = float(offer["offers"]["price"])
                    listings.append(listing)
        except (json.JSONDecodeError, AttributeError, KeyError):
            continue

    # Try __NEXT_DATA__ (Next.js apps)
    for script in soup.select("script#__NEXT_DATA__"):
        try:
            data = json.loads(script.string or "")
            props = data.get("props", {}).get("pageProps", {})
            search_results = props.get("searchResults", props.get("listings", []))
            if isinstance(search_results, list):
                for item in search_results:
                    listing = {
                        "property": prop["name"],
                        "region": prop["region"],
                        "area": prop["area"],
                        "type": listing_type,
                        "source": "propertyguru",
                        "scraped_at": datetime.now().isoformat(),
                        "title": item.get("title", item.get("name", "")),
                        "price": item.get("price", {}).get("value") if isinstance(item.get("price"), dict) else item.get("price"),
                        "size_sqft": item.get("floorArea", item.get("floor_area")),
                        "bedrooms": item.get("bedrooms", item.get("beds")),
                        "bathrooms": item.get("bathrooms", item.get("baths")),
                    }
                    if listing.get("price") and listing.get("size_sqft"):
                        listing["price_psf"] = round(listing["price"] / listing["size_sqft"], 2)
                    listings.append(listing)
        except (json.JSONDecodeError, AttributeError, KeyError):
            continue

    return listings


def scrape_property_details():
    """Scrape detailed property info pages."""
    details = []

    for prop in ALL_PROPERTIES:
        slug = prop["propertyguru_slug"]
        prop_id = prop["propertyguru_id"]
        if not slug or not prop_id:
            continue

        url = f"https://www.propertyguru.com.my/condo/{slug}-{prop_id}"
        print(f"  [PropertyGuru] Details for {prop['name']}...")

        html = _get(url)
        if not html:
            continue

        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        detail = {
            "property": prop["name"],
            "region": prop["region"],
            "source": "propertyguru",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
        }

        # Price range
        price_match = re.search(
            r"(?:Price|Asking)\s*(?:Range)?\s*:?\s*RM\s*([\d,]+)\s*(?:-|to)\s*RM\s*([\d,]+)",
            text, re.IGNORECASE,
        )
        if price_match:
            detail["price_min"] = float(price_match.group(1).replace(",", ""))
            detail["price_max"] = float(price_match.group(2).replace(",", ""))

        # Total units
        units_match = re.search(r"(\d+)\s*(?:total\s*)?units", text, re.IGNORECASE)
        if units_match:
            detail["total_units"] = int(units_match.group(1))

        details.append(detail)
        time.sleep(RATE_LIMIT_DELAY)

    return details


def _parse_price(text):
    if not text:
        return None
    text = text.replace(",", "").replace(" ", "")
    match = re.search(r"RM\s*([\d.]+)", text)
    if match:
        return float(match.group(1))
    match = re.search(r"([\d]+)", text)
    if match:
        return float(match.group(1))
    return None


if __name__ == "__main__":
    print("=== PropertyGuru Scraper ===")
    sale = scrape_listings("sale")
    print(f"Sale: {len(sale)}")
    for l in sale[:3]:
        print(f"  {l.get('title')} | RM {l.get('price')} | {l.get('size_sqft')} sqft")

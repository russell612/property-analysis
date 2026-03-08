"""
iProperty.com.my scraper using curl_cffi.
"""
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests
from config import ALL_PROPERTIES, RATE_LIMIT_DELAY


def _get(url):
    resp = cffi_requests.get(url, impersonate="chrome", timeout=30)
    resp.raise_for_status()
    return resp.text


def scrape_listings(listing_type="sale"):
    """Scrape iProperty listings for target properties."""
    all_listings = []

    for prop in ALL_PROPERTIES:
        search_name = prop["name"].replace(" ", "+")
        area = prop["area"].lower().replace(" ", "-")

        if listing_type == "sale":
            url = f"https://www.iproperty.com.my/sale/kuala-lumpur/{area}/?q={search_name}"
        else:
            url = f"https://www.iproperty.com.my/rent/kuala-lumpur/{area}/?q={search_name}"

        print(f"  [iProperty] Scraping {listing_type} for {prop['name']}...")

        try:
            html = _get(url)
            soup = BeautifulSoup(html, "lxml")

            # iProperty may embed data in __NEXT_DATA__
            next_data = soup.select_one("script#__NEXT_DATA__")
            if next_data and next_data.string:
                listings = _extract_from_nextdata(next_data.string, prop, listing_type)
                all_listings.extend(listings)
                print(f"  Found {len(listings)} from __NEXT_DATA__")
            else:
                # Fallback to HTML parsing
                listings = _parse_html_listings(soup, prop, listing_type)
                all_listings.extend(listings)
                print(f"  Found {len(listings)} from HTML")

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)

    # Also try building-specific pages
    _scrape_building_pages(all_listings)

    return all_listings


def _extract_from_nextdata(script_text, prop, listing_type):
    """Extract listings from iProperty __NEXT_DATA__."""
    listings = []
    try:
        data = json.loads(script_text)
        page_props = data.get("props", {}).get("pageProps", {})

        # Navigate to listings in the JSON structure
        items = []
        for key in ["searchResults", "listings", "data", "results"]:
            val = page_props.get(key)
            if isinstance(val, list):
                items = val
                break
            elif isinstance(val, dict):
                for subkey in ["results", "listings", "items", "data"]:
                    sub = val.get(subkey)
                    if isinstance(sub, list):
                        items = sub
                        break
            if items:
                break

        for item in items:
            if not isinstance(item, dict):
                continue

            title = item.get("title", item.get("name", item.get("headline", "")))

            # Filter for matching property
            if title and not _matches_property(title, prop):
                continue

            listing = {
                "property": prop["name"],
                "region": prop["region"],
                "area": prop["area"],
                "type": listing_type,
                "source": "iproperty",
                "scraped_at": datetime.now().isoformat(),
                "title": title,
            }

            # Price
            price = item.get("price", item.get("priceValue", item.get("askingPrice")))
            if isinstance(price, dict):
                price = price.get("value", price.get("amount"))
            if price:
                try:
                    listing["price"] = float(price)
                except (ValueError, TypeError):
                    pass

            # Size
            size = item.get("floorSize", item.get("buildUpSize", item.get("builtUp", item.get("floorArea"))))
            if isinstance(size, dict):
                size = size.get("value", size.get("size"))
            if size:
                try:
                    listing["size_sqft"] = float(size)
                except (ValueError, TypeError):
                    pass

            listing["bedrooms"] = item.get("bedrooms", item.get("beds"))
            listing["bathrooms"] = item.get("bathrooms", item.get("baths"))

            url = item.get("url", item.get("detailUrl", item.get("slug", "")))
            if url and not url.startswith("http"):
                url = f"https://www.iproperty.com.my{url}"
            listing["url"] = url

            if listing.get("price") and listing.get("size_sqft") and listing["size_sqft"] > 0:
                listing["price_psf"] = round(listing["price"] / listing["size_sqft"], 2)

            listings.append(listing)

    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"    JSON error: {e}")

    return listings


def _parse_html_listings(soup, prop, listing_type):
    """Parse iProperty listings from HTML cards."""
    listings = []

    # Look for listing cards or price patterns
    text = soup.get_text(" ", strip=True)

    # Find all RM price patterns with context
    price_blocks = re.findall(
        r'([\w\s]+?(?:Bamboo|GenStarz|Gen Starz)[\w\s]*?)RM\s*([\d,]+)',
        text, re.IGNORECASE
    )

    for context, price in price_blocks:
        listing = {
            "property": prop["name"],
            "region": prop["region"],
            "area": prop["area"],
            "type": listing_type,
            "source": "iproperty",
            "scraped_at": datetime.now().isoformat(),
            "title": context.strip()[:100],
            "price": float(price.replace(",", "")),
        }
        listings.append(listing)

    return listings


def _scrape_building_pages(all_listings):
    """Scrape building-specific pages."""
    building_urls = {
        "Bamboo Hills Residences": "https://www.iproperty.com.my/building/bamboo-hills-residences-pty_289612/",
    }

    for prop in ALL_PROPERTIES:
        burl = building_urls.get(prop["name"])
        if not burl:
            continue

        print(f"  [iProperty] Building page for {prop['name']}...")
        try:
            html = _get(burl)
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)

            detail = {
                "property": prop["name"],
                "region": prop["region"],
                "source": "iproperty",
                "type": "building_info",
                "scraped_at": datetime.now().isoformat(),
            }

            price_match = re.search(
                r"(?:from|starting)\s*RM\s*([\d,]+)\s*(?:to|-)\s*RM\s*([\d,]+)",
                text, re.IGNORECASE,
            )
            if price_match:
                detail["price_min"] = float(price_match.group(1).replace(",", ""))
                detail["price_max"] = float(price_match.group(2).replace(",", ""))

            units_match = re.search(r"(\d+)\s*(?:total\s*)?units", text, re.IGNORECASE)
            if units_match:
                detail["total_units"] = int(units_match.group(1))

            all_listings.append(detail)

        except Exception as e:
            print(f"  Error: {e}")

        time.sleep(RATE_LIMIT_DELAY)


def _matches_property(title, prop):
    title_lower = title.lower()
    names = [prop["name"].lower()] + [n.lower() for n in prop.get("alt_names", [])]
    return any(name in title_lower for name in names)

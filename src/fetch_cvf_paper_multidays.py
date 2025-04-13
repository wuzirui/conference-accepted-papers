import argparse
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def scrape_conference_papers(conference, year, days):
    base_urls = ["https://openaccess.thecvf.com"]

    response = None
    used_base_url = ""

    # Initialize result JSON
    result = {
        "Conference Name": (
            f"{year} IEEE/CVF Conference on Computer Vision and Pattern Recognition"
            if conference == "CVPR"
            else f"{year} IEEE/CVF International Conference on Computer Vision"
        ),
        "Proceeding Name": (
            "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)"
            if conference == "CVPR"
            else "Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)"
        ),
        "Year": year,
        "Publisher": "IEEE",
        "Papers": [],
    }
    papers = []

    for day in days:
        url_suffix = f"/{conference}{year}?day={day}"

        # Attempt to fetch the webpage for each day
        for base_url in base_urls:
            try:
                url = base_url + url_suffix
                print(f"Attempting to access: {url}")
                response = requests.get(url)
                response.raise_for_status()
                used_base_url = base_url
                print(f"Successfully accessed: {url}")
                break
            except Exception as e:
                print(f"Failed to access {base_url}: {e}")

        if not response or response.status_code != 200:
            print(f"Unable to fetch {conference}{year} paper data for day {day}")
            continue

        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all paper entries
        paper_titles = soup.find_all("dt", class_="ptitle")
        print(f"Found {len(paper_titles)} papers")

        # Iterate through each paper
        for i, title_tag in enumerate(paper_titles):
            if (i + 1) % 100 == 0:
                print(f"Processing: {i + 1}/{len(paper_titles)}")

            # Extract title
            title_link = title_tag.find("a")
            if not title_link:
                continue

            title = title_link.text.strip()
            paper_url = title_link.get("href", "")

            # Build full URL
            if paper_url and not paper_url.startswith("http"):
                paper_url = urljoin(used_base_url, paper_url)

            # Extract author information
            authors_dd = title_tag.find_next("dd")
            if not authors_dd:
                continue

            # Extract author list
            author_forms = authors_dd.find_all("form", class_="authsearch")
            authors = []
            for form in author_forms:
                input_tag = form.find("input", {"name": "query_author"})
                if input_tag and "value" in input_tag.attrs:
                    author_name = input_tag["value"].strip()
                else:
                    # Fallback: Extract author name from <a> tag if input_tag is None
                    author_link = form.find("a")
                    author_name = author_link.text.strip() if author_link else None

                if author_name:
                    authors.append(author_name)

            # Extract bibtex information for pages, DOI, etc.
            bibtex_dd = authors_dd.find_next("dd")
            if not bibtex_dd:
                continue

            bibtex_div = bibtex_dd.find("div", class_="bibref")
            if not bibtex_div:
                continue

            bibtex_text = bibtex_div.text.strip()

            # Extract page information from bibtex
            pages_match = re.search(r"pages\s*=\s*{([^}]*)}", bibtex_text)
            pages = pages_match.group(1) if pages_match else ""

            # Extract DOI information from bibtex (if available)
            doi_match = re.search(r"doi\s*=\s*{([^}]*)}", bibtex_text)
            doi = doi_match.group(1) if doi_match else ""

            if i == 0:
                # Extract month
                month_match = re.search(r"month\s*=\s*{([^}]*)}", bibtex_text)
                month = month_match.group(1) if month_match else ""
                if month:
                    result["Month"] = month
                    print(f"Month: {month}")

            # Add paper information in the specified format
            paper_entry = {
                "Title": title,
                "Authors": authors,
                "Url": paper_url,
                "DOI": doi,
                "Pages": pages,
            }

            papers.append(paper_entry)

    # Remove duplicate papers by title
    unique_papers = {}
    for paper in papers:
        title = paper["Title"]
        if title not in unique_papers:
            unique_papers[title] = paper

    result["Papers"] = list(unique_papers.values())

    print(f"Successfully processed {len(result['Papers'])} unique papers")
    return result


def save_to_json(data, filename):
    """Save data to a JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data saved to {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape CVPR/ICCV/WACV papers.")
    parser.add_argument(
        "conference",
        type=str,
        choices=["CVPR", "ICCV", "WACV"],
        help="Conference name (CVPR, ICCV, or WACV)",
    )
    parser.add_argument(
        "date_info",
        type=str,
        nargs="+",
        help="Year, start month, start day, end month, and end day for the conference (e.g., 2020 10 29 11 01)",
    )
    args = parser.parse_args()

    year = args.date_info[0]
    start_month = args.date_info[1]
    start_day = int(args.date_info[2])
    end_month = args.date_info[3]
    end_day = int(args.date_info[4])

    # Generate all days between start and end
    import calendar
    from datetime import date, timedelta

    start_date = date(int(year), int(start_month), int(start_day))
    end_date = date(int(year), int(end_month), int(end_day))

    # Validate the days based on the calendar
    if not (1 <= start_day <= calendar.monthrange(int(year), int(start_month))[1]):
        raise ValueError(f"Invalid start day: {start_day} for {start_month}/{year}")
    if not (1 <= end_day <= calendar.monthrange(int(year), int(end_month))[1]):
        raise ValueError(f"Invalid end day: {end_day} for {end_month}/{year}")

    delta = timedelta(days=1)
    formatted_days = []
    while start_date <= end_date:
        formatted_days.append(start_date.strftime("%Y-%m-%d"))
        start_date += delta

    start_time = time.time()
    data = scrape_conference_papers(args.conference, year, formatted_days)
    if data:
        output_filename = f"conf/{args.conference.upper()}/{year}.json"
        save_to_json(data, output_filename)
        print(f"Total time: {time.time() - start_time:.2f} seconds")
    else:
        print("Data scraping failed")

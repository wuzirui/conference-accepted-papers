import argparse
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def scrape_conference_papers(conference, year):
    base_urls = ["https://openaccess.thecvf.com"]
    url_suffix = f"/{conference}{year}?day=all"

    response = None
    used_base_url = ""

    # Attempt to fetch the webpage
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
        print(f"Unable to fetch {conference}{year} paper data")
        return None

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # Initialize result JSON
    result = {
        "Conference Name": f"{year} IEEE/CVF Conference on Computer Vision and Pattern Recognition" if conference == "CVPR" else f"{year} IEEE/CVF International Conference on Computer Vision",
        "Proceeding Name": "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)" if conference == "CVPR" else "Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)",
        "Year": year,
        "Publisher": "IEEE",
        "Papers": []
    }

    papers = []
    # Find all paper entries
    paper_titles = soup.find_all('dt', class_='ptitle')
    print(f"Found {len(paper_titles)} papers")

    # Iterate through each paper
    for i, title_tag in enumerate(paper_titles):
        if (i + 1) % 100 == 0:
            print(f"Processing: {i + 1}/{len(paper_titles)}")

        # Extract title
        title_link = title_tag.find('a')
        if not title_link:
            continue

        title = title_link.text.strip()
        paper_url = title_link.get('href', '')

        # Build full URL
        if paper_url and not paper_url.startswith('http'):
            paper_url = urljoin(used_base_url, paper_url)

        # Extract author information
        authors_dd = title_tag.find_next('dd')
        if not authors_dd:
            continue

        # Extract author list
        author_forms = authors_dd.find_all('form', class_='authsearch')
        authors = []
        for form in author_forms:
            input_tag = form.find('input', {'name': 'query_author'})
            if input_tag and 'value' in input_tag.attrs:
                author_name = input_tag['value'].strip()
            else:
                # Fallback: Extract author name from <a> tag if input_tag is None
                author_link = form.find("a")
                author_name = author_link.text.strip() if author_link else None
            if author_name:
                authors.append(author_name)

        # Extract bibtex information for pages, DOI, etc.
        bibtex_dd = authors_dd.find_next('dd')
        if not bibtex_dd:
            continue

        bibtex_div = bibtex_dd.find('div', class_='bibref')
        if not bibtex_div:
            continue

        bibtex_text = bibtex_div.text.strip()

        # Extract page information from bibtex
        pages_match = re.search(r'pages\s*=\s*{([^}]*)}', bibtex_text)
        pages = pages_match.group(1) if pages_match else ""

        # Extract DOI information from bibtex (if available)
        doi_match = re.search(r'doi\s*=\s*{([^}]*)}', bibtex_text)
        doi = doi_match.group(1) if doi_match else ""

        if i == 0:
            # Extract month
            month_match = re.search(r'month\s*=\s*{([^}]*)}', bibtex_text)
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
            "Pages": pages
        }

        papers.append(paper_entry)

    result['Papers'] = papers

    print(f"Successfully processed {len(result['Papers'])} papers")
    return result

def save_to_json(data, filename):
    """Save data to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape CVPR/ICCV/WACV papers.")
    parser.add_argument("conference", type=str, choices=["CVPR", "ICCV", "WACV"], help="Conference name (CVPR or ICCV)")
    parser.add_argument("year", type=int, help="Year of the conference")
    args = parser.parse_args()

    start_time = time.time()
    data = scrape_conference_papers(args.conference, args.year)
    if data:
        output_filename = f"conf/{args.conference.upper()}/{args.year}.json"
        save_to_json(data, output_filename)
        print(f"Total time: {time.time() - start_time:.2f} seconds")
    else:
        print("Data scraping failed")

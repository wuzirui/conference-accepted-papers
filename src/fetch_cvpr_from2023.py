import json
import argparse
import requests
from bs4 import BeautifulSoup


def fetch_cvpr_metadata(url, output_file, year):
    try:
        # Fetch the webpage content
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP issues
        html_content = response.text

        # # save the HTML content to a file
        # with open(f"cvpr_{year}.html", "w", encoding="utf-8") as f:
        #     f.write(html_content)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract paper titles and authors
        papers = []
        for row in soup.find_all("tr"):  # Iterate over table rows
            title_tag = row.find("strong") or row.find(
                "a"
            )  # Find the title in <strong> or <a>
            authors_tag = row.find(
                "div", class_="indented"
            )  # Find authors in <div class="indented">

            if title_tag and authors_tag:
                title = title_tag.get_text(strip=True)
                # Split authors by "·" and strip whitespace
                authors = [
                    author.strip()
                    for author in authors_tag.get_text(strip=True).split("·")
                ]
                papers.append({"Title": title, "Authors": authors})
        conf = {
            "Conference Name": f"{year} IEEE/CVF Conference on Computer Vision and Pattern Recognition",
            "Proceeding Name": "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition",
            "Year": year,
            "Publisher": "IEEE",
            "Papers": papers,
        }

        # Save the metadata to a JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)
        print(f"Fetched {len(papers)} papers from the URL.")

        print(f"Metadata successfully saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch CVPR metadata.")
    parser.add_argument("--year", type=int, help="Year of the CVPR conference")
    args = parser.parse_args()
    year = int(args.year)

    # Validate the year 
    assert year >= 2023, "Year must be 2023 or later."

    # URL of the CVPR Accepted Papers page
    url = f"https://cvpr.thecvf.com/Conferences/{args.year}/AcceptedPapers"
    # Output JSON file
    output_file = f"conf/CVPR/{args.year}.json"

    fetch_cvpr_metadata(url, output_file, args.year)

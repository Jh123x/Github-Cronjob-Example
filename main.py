import requests     # To get the data from the API
import datetime     # To get the current date
import logging      # To log our flow
import os           # File operations
import re           # Clean non ascii

from urllib.parse import quote
from typing import Dict


MD_DIR = "docs"
CONTENT_DIR = os.path.join(MD_DIR, "index.md")
DATE_FORMAT = "%Y-%m-%d"
TITLE_FORMAT = "{date}_{title}.md"
DATA_URL = "https://xkcd.com/{page_no}/info.0.json"
MARKDOWN_FORMAT = """
# XKCD Comic for day {date}

## {title}

![{title}]({img_url} "{alt}")

[Visit the original page](https://xkcd.com/{num}/)
"""
CONTENT_PAGE_SPLIT = f"| {'-'*10} | {'-'*50} | {'-'*142} |"


def clean_title(title: str) -> str:
    return re.sub(r'[^\x00-\x7f]',r'', title).replace(" ", "_").replace(":","")


def generate_file_name(title: str, date: str) -> str:
    """Generate the file name for the markdown file to be written"""
    return TITLE_FORMAT.format(date=date, title=clean_title(title))


def generate_markdown(title: str, img_url: str, alt: str, num: int, date: str) -> str:
    """Generate the markdown content"""
    return MARKDOWN_FORMAT.format(date=date, title=title, img_url=img_url, alt=alt, num=num)


def generate_content_line(title: str, date: str, url_path: str) -> str:
    """Generate the content line for the content page"""
    link_format = f"[Link](./{quote(url_path)} \"{title}\")"
    return f"| {date:10} | {title:50} | {link_format:142} |"


def insert_to_content_page(title: str, date: str, file_name: str):
    """Insert the markdown content into the content page"""
    with open(CONTENT_DIR, "r") as file:
        data = file.read()

    headers, contents = data.split(CONTENT_PAGE_SPLIT)
    result = [headers.strip(), CONTENT_PAGE_SPLIT.strip()]
    line_set = set(filter(lambda x: x.strip(), contents.split("\n")))

    new_line = generate_content_line(title, date, file_name)
    line_set.add(new_line)
    lines = list(line_set)
    lines.sort(key=lambda x: x.split("|")[1], reverse=True)
    result.extend(lines)
    with open(CONTENT_DIR, "w") as f:
        f.write("\n".join(filter(lambda x: len(x.strip()) > 0, result)))
        f.write("\n")


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    current_time = datetime.datetime.now()
    project_start_date = datetime.datetime(2024, 3, 17)
    day_since_creation = current_time - project_start_date

    for page_no in range(1, day_since_creation.days):
        current_time = project_start_date + datetime.timedelta(days=page_no)
        # Call the api
        with requests.Session() as session:
            response = session.get(
                DATA_URL.format(page_no=page_no),
            )

            if response.status_code >= 400:
                logger.critical(f"Failed to get the data from the API. Status code: {response.status_code}")
                exit(1)

            data: Dict[str, str] = response.json()

        # Extract information
        title = data.get("title", "No title")
        img_url = data.get("img", "No image")
        alt = data.get("alt", "No alt")
        num = data.get("num", "1")

        # Create the file
        date_str = current_time.strftime(DATE_FORMAT)
        file_name = generate_file_name(title, date_str)

        with open(os.path.join(MD_DIR, file_name), "w") as file:
            file.write(
                generate_markdown(title, img_url, alt, int(num), date_str),
            )

        # Update the content page
        insert_to_content_page(title, date_str, file_name.strip(".md"))

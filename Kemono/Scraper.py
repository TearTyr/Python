from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import requests
import os
import urllib.parse

SERVICES = {
    "fanbox": "https://kemono.su/fanbox/user/",
    "patreon": "https://kemono.su/patreon/user/",
    "gumroad": "https://kemono.su/gumroad/user/"
}

def download(url, filename):
    with open(filename, "wb") as f:
        response = requests.get(url)
        f.write(response.content)

def download_all(urls, filenames):
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download, urls, filenames)

def scrape_attachments(post_url, artist_name):
    base_url = "https://kemono.su"
    full_url = base_url + post_url
    response = requests.get(full_url)
    soup = BeautifulSoup(response.content, "html.parser")
    attachments = soup.find_all("a", class_="post__attachment-link")
    urls = []
    filenames = []
    if attachments:
        for attachment in attachments:
            attachment_url = attachment.get("href")
            filename_with_download = urllib.parse.unquote(attachment.text)
            filename = filename_with_download.replace("Download ", "")
            filename = filename.encode('utf-8').decode('utf-8-sig', errors='replace')
            filename = filename.replace("?", "_").replace("=", "_")
            filename = os.path.join("Scraped", artist_name, filename.strip())  # Use os.path.join for path joining
            urls.append(attachment_url)
            filenames.append(filename)
        if urls:
            print(f"Found attachments in post: {full_url}")
            return urls, filenames
        else:
            print(f"No attachments found in post: {full_url}")
            return None, None
    else:
        print(f"Skipping post without attachments: {post_url}")
        return None, None

def get_name(user_id, service):
    try:
        response = requests.get(SERVICES[service] + user_id)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, "html.parser")
        name_element = soup.find("span", itemprop="name")
        if name_element:
            return name_element.text.strip()
        else:
            return "Unknown Artist"
    except requests.RequestException:
        return "Unknown Artist"

def get_posts(user_id, service):
    try:
        response = requests.get(SERVICES[service] + user_id)
        response.raise_for_status()  
        soup = BeautifulSoup(response.content, "html.parser")
        posts = soup.find_all("article", class_="post-card post-card--preview")
        return posts
    except requests.RequestException:
        return []

def auto_switch(user_id, services):
    for service in services:
        name = get_name(user_id, service)
        if name != "Unknown Artist":
            return service, name
    return None, "Unknown Artist"

user_id_to_scrape = "12561573"  # User to change
services_to_try = ["fanbox", "patreon", "gumroad"]

service_to_scrape, artist_name = auto_switch(user_id_to_scrape, services_to_try)

if service_to_scrape:
    print(f"Service selected: {service_to_scrape}")
    print(f"Artist Name: {artist_name}")

    posts = get_posts(user_id_to_scrape, service_to_scrape)

    folder_path = f"Scraped/{artist_name}"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    total_posts_scanned = 0
    posts_with_attachments = 0

    attachment_urls = []
    attachment_filenames = []

    for post in posts:
        post_url = post.find("a")["href"]
        total_posts_scanned += 1
        urls, filenames = scrape_attachments(post_url, artist_name)
        if urls:
            attachment_urls.extend(urls)
            attachment_filenames.extend(filenames)
            posts_with_attachments += 1

    print(f"Total posts scanned: {total_posts_scanned}")
    print(f"Posts with attachments found: {posts_with_attachments}")

    if attachment_urls:
        print("Starting download...")
        download_all(attachment_urls, attachment_filenames)
        print("Download completed.")
    else:
        print("No attachments found to download.")
else:
    print("Failed to fetch artist information.")

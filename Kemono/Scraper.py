import requests
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor
import urllib.parse

def download_file(url, filename):
    with open(filename, "wb") as f:
        response = requests.get(url)
        f.write(response.content)

def download_files(urls, filenames):
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(download_file, urls, filenames)

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
            filename_with_download = urllib.parse.unquote(attachment.text)  # Extract filename from the <a>
            filename = filename_with_download.replace("Download ", "")
            filename = filename.encode('utf-8').decode('utf-8-sig', errors='replace')
            filename = filename.replace("?", "_").replace("=", "_")
            urls.append(attachment_url)
            filenames.append(f"Scraped/{artist_name}/{filename.strip()}")
        if urls:
            print(f"Found attachments in post: {full_url}")
            return urls, filenames
        else:
            print(f"No attachments found in post: {full_url}")
            return None, None
    else:
        print(f"Skipping post without attachments: {post_url}")
        return None, None

def get_artist_name(user_id):
    response = requests.get(f"https://kemono.su/fanbox/user/{user_id}")
    soup = BeautifulSoup(response.content, "html.parser")
    artist_name_element = soup.find("span", itemprop="name")
    if artist_name_element:
        return artist_name_element.text.strip()
    else:
        return "Unknown Artist"

def get_user_posts(user_id):
    response = requests.get(f"https://kemono.su/fanbox/user/{user_id}")
    soup = BeautifulSoup(response.content, "html.parser")
    posts = soup.find_all("article", class_="post-card post-card--preview")
    return posts

user_id_to_scrape = "338517" # Change user id
posts = get_user_posts(user_id_to_scrape)
artist_name = get_artist_name(user_id_to_scrape)

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
    download_files(attachment_urls, attachment_filenames)
    print("Download completed.")
else:
    print("No attachments found to download.")

import os
import random
import smtplib
import time
from datetime import datetime, timedelta
from email.message import EmailMessage

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-blink-features=AutomationControlled")
options.binary_location = "/usr/bin/google-chrome"

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

jobs_set = set()
jobs_list = []
MAX_JOBS = 30

job_keywords = [
    "full stack developer", "software engineer", "full stack engineer",
    "frontend developer", "software developer", "javascript developer"
]

one_month_ago = datetime.now() - timedelta(days=30)

for keyword in job_keywords:
    for page in range(0, 250, 25):
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location=Hyderabad%2C%20India&start={page}"
        driver.get(url)
        time.sleep(random.uniform(5, 10))

        for _ in range(7):
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(random.uniform(2, 5))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")

        for job in job_cards:
            title = job.find("h3", class_="base-search-card__title").text.strip().lower()
            company = job.find("h4", class_="base-search-card__subtitle").text.strip()
            job_link = job.find("a", class_="base-card__full-link")["href"]

            if "java " in title or title.endswith(" java"):
                continue

            date_posted_elem = job.find("time")
            if date_posted_elem:
                date_posted_text = date_posted_elem["datetime"]
                date_posted = datetime.strptime(date_posted_text, "%Y-%m-%d")
                if date_posted < one_month_ago:
                    continue

            if (title, company) in jobs_set:
                continue
            jobs_set.add((title, company))

            jobs_list.append({
                "Title": title.title(),
                "Company": company,
                "Date Posted": date_posted_text,
                "Link": f'=HYPERLINK("{job_link}", "Job Link")'
            })

        if len(jobs_list) >= MAX_JOBS:
            break
    if len(jobs_list) >= MAX_JOBS:
        break

driver.quit()

jobs_list.sort(key=lambda x: x["Date Posted"], reverse=True)

file_name = "filtered_linkedin_jobs.xlsx"
df = pd.DataFrame(jobs_list)
df.to_excel(file_name, index=False, engine="openpyxl")

def send_email():
    sender_email = os.getenv("EMAIL_USERNAME")
    sender_password = os.getenv("EMAIL_PASSWORD")
    receiver_email = "nagacharankumarreddy@gmail.com"

    subject = "Job Listings - Report"
    body = f"""
    Hi Charan,

    Here is the latest job listing extracted from LinkedIn.
    The attached file contains {len(jobs_list)} jobs.

    Best regards,
    Automated Job Scraper
    """

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.set_content(body)

    with open(file_name, "rb") as attachment:
        msg.add_attachment(attachment.read(), maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=file_name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

send_email()

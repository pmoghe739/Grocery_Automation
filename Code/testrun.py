import time
import io
import random

import requests
from googleapiclient.http import MediaIoBaseDownload
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
import imaplib, email
import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type

# todo:
# validate words received from google drive file.

def get_otp_from_gmail(gmail_service):
    msgs = search_messages(gmail_service, 'from:alerts@bigbasket.com')
    message = gmail_service.users().messages().get(userId='me', id=msgs[0]['id']).execute()
    snippet = message['snippet']
    print(message['snippet'])
    if snippet.startswith('Login using OTP:'):
        index = snippet.find(":")
        otp = snippet[index+2: index+8]
        print(otp)
        return otp

def gmail_authenticate():
    SCOPES = ['https://mail.google.com/','https://www.googleapis.com/auth/drive']
    our_email = 'pmoghe739@gmail.com'
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds), build('drive', 'v3', credentials=creds)

def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages
def goto_search(driver):
    return driver.find_element_by_id('input')

def get_items_from_shopping_list():
    # Key value storage server = http: // keyvalue.immanuel.co /
    app_key = 'nb4c46nc'
    key_name = 'shopping_list'
    r = requests.get('https://keyvalue.immanuel.co/api/KeyVal/GetValue/'+app_key+'/'+key_name)
    items = r.text
    return items.split(',')

def get_items_from_shopping_list_v2(drive_service):
    page_token = None
    while True:
        response = drive_service.files().list(q="name='sample_list.txt'",
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name)',
                                              pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            print('Found file: %s (%s)' % (file.get('name'), file.get('id')))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    file_id = response.get('files', [])[0].get('id')
    request = drive_service.files().get_media(fileId=file_id)
    # fname = "sample_list_"+str(random.random())+".txt"
    fname = "sample_list.txt"
    fh = io.FileIO(fname, 'w')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    items = []
    with open(fname) as f:
        line = f.readline()
        items = line.split(',')
    return items



driver = webdriver.Chrome(ChromeDriverManager().install())
driver.maximize_window()
driver.get("https://www.bigbasket.com/auth/login/?nc=close")
time.sleep(4)
select_email_button = driver.find_element_by_xpath(".//*[text()='Login using Email Address']")
select_email_button.click()
time.sleep(1)
mobile_number_input = driver.find_element_by_id('otpEmail')
mobile_number_input.send_keys('pmoghe739@gmail.com')
mobile_number_input.send_keys(Keys.ENTER)
time.sleep(5)
gmail_service, drive_service = gmail_authenticate()
otp = get_otp_from_gmail(gmail_service)
otp_field = driver.find_element_by_id('otp')
otp_field.send_keys(otp)
time.sleep(1)
verify_continue_button = driver.find_element_by_xpath(".//*[text()='Verify & Continue']")
verify_continue_button.click()
time.sleep(4)
driver.get('https://www.bigbasket.com/')
time.sleep(6)
search_bar = goto_search(driver)
time.sleep(3)
missing_inventory = get_items_from_shopping_list()
for item in missing_inventory:
    search_bar.clear()
    search_bar.send_keys(item)
    time.sleep(3)
    top_result_add_btn = driver.find_element_by_xpath(".//*[@qa='addBtnAS']")
    top_result_add_btn.click()
    time.sleep(4)
#
print(missing_inventory)
# search_bar.send_keys('banana')


# driver.close()




'''
    This project has a separate environment called myenv
    To activate myenv execute the command conda activate myenv
'''
import requests
from bs4 import BeautifulSoup
import time
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import jinja2

# URL for worldometer for country wise data
wm_url = "https://www.worldometers.info/coronavirus/country/us/"
# URL for michigan.gov for state wise data
mich_url = "https://www.michigan.gov/coronavirus/0,9753,7-406-98163_98173---,00.html"

port = 465  # For SSL
smtp_server = "smtp.gmail.com"
sender_email = "bhargavkuchipudi0@gmail.com"  # Enter your address
password = input("Please enter your gmail password: ")

init=True

templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "status.html"

previous_values = {
    'usa_affected': 0,
    'usa_new_cases': 0,
    'usa_total_deaths': 0,
    'mi_affected': 0,
    'mi_new_cases': 0,
    'mi_total_deaths': 0,
    'mi_position': 0,
    'county_affected': 0,
    'county_deaths': 0
}

current_values = {
    'usa_affected': 0,
    'usa_new_cases': 0,
    'usa_total_deaths': 0,
    'mi_affected': 0,
    'mi_new_cases': 0,
    'mi_total_deaths': 0,
    'mi_position': 0,
    'county_affected': 0,
    'county_deaths': 0
}


def get_details(state_name, county):
    try:
        us_page = requests.get(wm_url)
        us_soup = BeautifulSoup(us_page.content, 'html.parser')
        usa_table = us_soup.find(id="usa_table_countries_today").find_all('tbody')[0].find_all('tr')
        usa_total = usa_table[0].find_all('td')
        current_values['usa_affected'] = usa_total[1].text.strip().replace(',','').replace('+', '')
        current_values['usa_new_cases'] = usa_total[2].text.strip().replace(',','').replace('+', '')
        current_values['usa_total_deaths'] = usa_total[3].text.strip().replace(',','').replace('+', '')
        for i, state in enumerate(usa_table):
            r = state.find_all('td')
            if (r[0].text.strip().lower() == state_name):
                current_values['mi_affected'] = r[1].text.strip().replace(',', '')
                current_values['mi_new_cases'] = r[2].text.strip().replace(',', '')
                current_values['mi_total_deaths'] = r[3].text.strip().replace(',', '')
                current_values['mi_position'] = i

        state_page = requests.get(mich_url)
        state_soup = BeautifulSoup(state_page.content, 'html.parser')
        state_data = state_soup.find_all('table')[0].find_all('tbody')[0].find_all('tr')
        for row in state_data:
            r = row.find_all('td')
            if (r[0].text.strip().lower() == county):
                current_values['county_affected'] = r[1].text.replace(',', '')
                current_values['county_deaths'] = r[2].text.replace(',', '')

        for key in current_values:
            if current_values[key] == '':
                current_values[key] = 0
            else:
                current_values[key] = int(current_values[key])

        return current_values
    except:
        f = open('log.txt', 'a')
        f.write("<<<<<<<<<<<<<<<<<<Error occured in scrapping the file:" + str(datetime.now()) + '>>>>>>>>>>>>>>>>>>>>>\n')
        f.close()
        return False
    

    

def send_email(message, receiver_email):
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        f = open('log.txt', 'a')
        f.write("Mail sent on:" + str(datetime.now()) + '\n')
        f.close()
        for key in current_values:
            previous_values[key] = current_values[key]

def validate(obj):
    global init
    if init:
        init = False
        return True
    else:
        for key in obj:
            if obj[key] != previous_values[key]:
                return True
        return False


def main():
    mails = open('mail.txt')
    receiver_email = mails.read().split()  # Enter receiver address
    state, county = 'michigan', 'isabella'
    state_obj = get_details(state, county)
    if state_obj == False:
        return
    update_status = validate(state_obj)
    if update_status:
        template = templateEnv.get_template(TEMPLATE_FILE)
        t = template.render(usa_affected=state_obj['usa_affected'],
                        usa_new_cases=state_obj['usa_new_cases'],
                        usa_total_deaths=state_obj['usa_total_deaths'],
                        mi_affected=state_obj['mi_affected'],
                        mi_new_cases=state_obj['mi_new_cases'],
                        mi_total_deaths=state_obj['mi_total_deaths'],
                        county_affected=state_obj['county_affected'],
                        county_deaths=state_obj['county_deaths'])

        message = MIMEMultipart()
        message['Subject'] = 'COVID-19 UPDATE'
        message['From'] = 'bhargavkuchipudi0@gmail.com'
        message['To'] = ','.join(receiver_email)

        message.attach(MIMEText(t, "html"))
        msgBody = message.as_string()
        send_email(msgBody, receiver_email)
    else:
        f = open('log.txt', 'a')
        f.write(str(current_values)+'\n')
        f.close()

def timer():
    while True:
        main()
        time.sleep(900)
    

if __name__ == '__main__':
    timer()
from openai import OpenAI
import streamlit as st
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup
import random


OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_ASSISTANT_ID = st.secrets["OPENAI_ASSISTANT_ID"]
SPACESERP_API_KEY = st.secrets["SPACESERP_API_KEY"]
ROCKETSCRAPE_API_KEY = st.secrets["ROCKETSCRAPE_API_KEY"]


def get_serp_result(topic, number_of_result_from_serp = 10, from_news=True, period="y", indonesian_domain = True):
    location_parameter = ""
    period_parameter = ""
    tab_parameter = ""
    page_size_parameter = ""
    if indonesian_domain:
        location_parameter = "&location=Jakarta%2CJakarta%2CIndonesia&domain=google.co.id&gl=id&hl=id"
    if period not in ["h", "d", "w", "m", "y"]:
        return {
            "error" : "Invalid period"
        }
    period_parameter = "&period=qdr%3A{}".format(period)
    if from_news:
        tab_parameter = "&tbm=nws"
    page_size_parameter = "&pageSize={}".format(number_of_result_from_serp)
    topic_parameter = urllib.parse.quote("+".join(topic.split(" ")), safe='')
    api_response = requests.get("https://api.spaceserp.com/google/search?apiKey={}&q={}&resultFormat=json{}{}{}{}".format(
        SPACESERP_API_KEY, topic_parameter, location_parameter, period_parameter, tab_parameter, page_size_parameter
    )).json()
    return api_response

def get_link_content(link):
    raw_html = requests.get("https://api.rocketscrape.com/?apiKey={}&render=true&url={}".format(ROCKETSCRAPE_API_KEY, link)).content
    soup = BeautifulSoup(raw_html, features="lxml")
    return soup.select_one("body").getText()

def get_sentiment(negative_sentiment, positive_sentiment, topic, article_content, max_attempt=60, sleep_in_between=2, override=2.5):
    time.sleep(1)

    return random.gauss(override,1)
    client = OpenAI(api_key=OPENAI_API_KEY)
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id

    content = """
    0 represents {} and 5 represents {},  with topic : {}

    ----------
    
    {}
    """.format(negative_sentiment, positive_sentiment, topic, article_content)
    client.beta.threads.messages.create(
        thread_id=st.session_state["thread_id"],
        role="user",
        content= content
    )
    run = client.beta.threads.runs.create(
        thread_id=st.session_state["thread_id"],
        assistant_id=OPENAI_ASSISTANT_ID
    )

    last_status = "in_progress"
    while last_status != "completed" and max_attempt > 0:
        time.sleep(sleep_in_between)
        check = client.beta.threads.runs.retrieve(
            thread_id=st.session_state["thread_id"],
            run_id=run.id
        )
        last_status = check.status
        max_attempt -= 1
    if last_status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state["thread_id"]
        )
        response = messages.data[0].content[0].text.value
        return response
    else:
        print("last_status : {}".format(last_status))
        print(check)
        return "ERROR"
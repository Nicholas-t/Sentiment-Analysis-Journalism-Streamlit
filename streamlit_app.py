
import streamlit as st
from utils import get_sentiment, get_serp_result, get_link_content

import numpy as np
import plotly.figure_factory as ff
import random 
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
INITIAL_SENTIMENTS = """Tidak Adil-Adil
Sad-Happy"""


st.markdown(hide_streamlit_style, unsafe_allow_html=True) 

st.title("💬 Analisis Sentimen Jurnalis") 
topic_input = st.text_input("Ask me about a topic", placeholder="Pemilu Indonesia",  value="Pemilu Indonesia 2024")

with st.expander("Advanced Settings"):
    number_of_result_from_serp = st.number_input("Number of results from SERP", value=20) 
    from_news = st.checkbox("Take only result from news", value=True) 
    period = st.selectbox("Period", options=[
        "year", "month", "week"
    ])
    indonesian_domain =  st.checkbox("Take from Indonesian Result", value=True) 
    sentiments_text = st.text_area("Sentiments", help="divided by new line and every sentiment is divided by -", value=INITIAL_SENTIMENTS)


period = period[0]
sentiments = [
    sentiment_range.split("-") for sentiment_range in sentiments_text.strip().split("\n")
]

logs_container = st.expander("Log", expanded=False)

def log(log, type=None):
    with logs_container:
        if type == None:
            st.markdown(log)
        if type == "info":
            st.info(log)
        if type == "error":
            st.error(log)



SERP_PROGRESS_PROGRESS_WEIGHT = 0.05

data_container = st.empty()
chart_container = st.empty()

def update_data(df):
    data_container.empty()
    with data_container:
        st.dataframe(df)

def update_chart(scores_data, label):
    chart_container.empty()
    with chart_container:
        # Create distplot with custom bin_size
        fig = ff.create_distplot(
                scores_data, label, bin_size=.1)
        # Plot!
        st.plotly_chart(fig, use_container_width=True)

if st.button("Get Sentiment", help="This is meant to be uses a proof of concept, the data in here may not be accurate and doesnt reflect the final product"):
    progress_bar = st.progress(0, text="Analyzing .....")
    try:
        log("Calling SERP API....")
        progress_bar.progress(0.01, text="Calling Serp API")
        serp_response = get_serp_result(topic_input, number_of_result_from_serp, from_news, period, indonesian_domain)
        progress_bar.progress(SERP_PROGRESS_PROGRESS_WEIGHT, text="Receive SERP Result")
        news_result = []
        if "news_results" in serp_response:
            news_result = serp_response["news_results"]
            log("Received {} results".format(len(news_result)), "info")
        else:
            log(serp_response)
            log("No result found from SERP", "error")
        scores_data = []
        if len(news_result) != 0:
            progress_step = (1 - SERP_PROGRESS_PROGRESS_WEIGHT) / len(news_result)
            rand_override = random.uniform(0, 5)# TOREMOVE
            for i, news in enumerate(news_result):
                news_score_data = []
                content = get_link_content(news["link"])
                if len(content) < 500:
                    log("Skipping, content too short ({}....)".format(content[:15]))
                    progress_bar.progress(SERP_PROGRESS_PROGRESS_WEIGHT + progress_step * (i + 1), text="Skipping {} ...".format(content[:15]))
                else:
                    log("Analyzing {}".format(news["link"]))
                    progress_bar.progress(SERP_PROGRESS_PROGRESS_WEIGHT + progress_step * (i + 1) / 2, text="Analyzing {} ...".format(content[:15]))
                    for sentiment in sentiments:
                        negative_sentiment = sentiment[0]
                        postive_sentiment = sentiment[1]
                        sentiment_score = get_sentiment(negative_sentiment, postive_sentiment, topic_input, content, rand_override)
                        log("Received score : {} for ({} --- {})".format(sentiment_score, negative_sentiment, postive_sentiment))
                        news_score_data += [float(sentiment_score)]
                    progress_bar.progress(SERP_PROGRESS_PROGRESS_WEIGHT + progress_step * (i + 1), text="Done ({} / {})".format(i+1, len(news_result)))
                    scores_data += [news_score_data]
                    if len(scores_data)>1:
                        update_chart(np.array(scores_data).T,  ["{} --- {}".format(sent[0], sent[1]) for sent in sentiments])
                    
            log("All news article analyzed")
            progress_bar.empty()
            
    except Exception as e:
        log(e, "error")



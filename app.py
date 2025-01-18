from flask import Flask, render_template, redirect, url_for, request, session
import pandas as pd
import pandas as pd
from datetime import datetime, timedelta, timezone
import os
import secrets
import operator
from googleapiclient.discovery import build

app = Flask(__name__)
UPLOAD_FOLDER = 'jsons'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json'}
app.secret_key = secrets.token_hex()

def getInfo(videoIds, time):
    if time not in session:
        channels = {}
        tags = {}
        youtube = build('youtube', 'v3', developerKey='AIzaSyA41op1Oc9MzPveNTil00QuqwxvgDqPOwY')
        for videoId in videoIds:
            try:
                request = youtube.videos().list(part='snippet,topicDetails', id=videoId)
                response = request.execute()
                if "items" not in response:
                    continue
                response = response["items"]
                if len(response) == 0:
                    continue
                if 'snippet' in response[0]:
                    if 'channelTitle' in response[0]['snippet']:
                        channel = response[0]['snippet']['channelTitle']
                        if channel not in channels:
                            channels[channel] = 1
                        else:
                            channels[channel] += 1
                if 'topicDetails' in response[0]:
                    if 'topicCategories' in response[0]['topicDetails']:
                        categories = response[0]['topicDetails']['topicCategories']
                        for category in categories:
                            if category not in tags: 
                                tags[category] = 1
                            else:
                                tags[category] += 1
            except Exception:
                pass
        session[time] =  [channels, tags]
    else:
        channels = session[time][0]
        tags = session[time][1]
    return (channels, tags)

def is_within_year(dt, year):
    return dt.year == year

def process(df, time):
    filtered_history = df[df['details'].notnull() == False]
    filtered_history["test"] = filtered_history['titleUrl'].apply(lambda x: x.split("watch")[-1])
    filtered_history = filtered_history[filtered_history["test"].str[0] != "h"] 
    filtered_history['time'] = pd.to_datetime(filtered_history['time'], format='mixed')
    filtered_history = filtered_history[filtered_history.apply(lambda row: is_within_year(row['time'], int(time)), axis=1)]
    filtered_history_sort = filtered_history['titleUrl'].value_counts(ascending=False).reset_index()
    topVids = filtered_history_sort['titleUrl'].head(5).tolist()
    filtered_history['titleUrl'] = filtered_history['titleUrl'].apply(lambda x: x.split("=")[-1]) 
    topVids[:] = ["https://youtube.com/embed/" + vid.split("=")[1] for vid in topVids]
    channelData, tagData = getInfo(filtered_history['titleUrl'].tolist(), time)
    return (topVids, dict(sorted(channelData.items(), key=operator.itemgetter(1), reverse=True)[:5]), dict(sorted(tagData.items(), key=operator.itemgetter(1), reverse=True)[:5]))
   

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/success', methods = ['GET', 'POST'])   
def success():   
    if request.method == 'POST':   
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            session['uploaded_data_file_path'] = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            history = pd.read_json(session['uploaded_data_file_path'])
            history['time'] = pd.to_datetime(history['time'], format='mixed')
            years = history['time'].dt.year
            unique_years = years.unique()
            return render_template("data.html", years=unique_years) 
    return render_template("data.html", years=[]) 

@app.route('/show_data')
def showData():
    # Uploaded File Path
    data_file_path = session.get('uploaded_data_file_path', None)
    # read json
    time = request.args.get("time") 
    uploaded_df = pd.read_json(data_file_path)
    topVids, channels, tags = process(uploaded_df, time)
    orderedTags = [key.split("/")[-1].replace("_", " ") for key in tags]
    return render_template('show_data.html',
                           vids=topVids, channel=channels, tag=orderedTags)
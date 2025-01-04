from flask import Flask, render_template, redirect, url_for, request, session
import pandas as pd
import datetime
import pandas as pd
from datetime import datetime
import os
import secrets
from googleapiclient.discovery import build

app = Flask(__name__)
UPLOAD_FOLDER = 'jsons'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json'}
app.secret_key = secrets.token_hex()

def getInfo(videoIds):
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
      return
  return (channels, tags)

def process(df):
    filtered_history = df[df['details'].notnull() == False]
    filtered_history["test"] = filtered_history['titleUrl'].apply(lambda x: x.split("watch")[-1])
    filtered_history = filtered_history[filtered_history["test"].str[0] != "h"] 
    filtered_history['time'] = pd.to_datetime(filtered_history['time'], format='mixed')
    this_month = filtered_history.loc[(filtered_history['time'].dt.year == datetime.now().year-1)].head(100)
    this_month['titleUrl'] = this_month['titleUrl'].apply(lambda x: x.split("=")[-1]) 
    channelData, tagData = getInfo(this_month['titleUrl'].tolist())
    return (sorted(channelData.items(), key=lambda x: x[1], reverse=True), sorted(tagData.items(), key=lambda x: x[1], reverse=True))
   

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/success', methods = ['POST'])   
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
            return render_template("data.html", name = filename) 
    return render_template('index.html')

@app.route('/show_data')
def showData():
    # Uploaded File Path
    data_file_path = session.get('uploaded_data_file_path', None)
    # read csv
    uploaded_df = pd.read_json(data_file_path)
    channels, tags = process(uploaded_df)
    return render_template('show_data.html',
                           channel=channels, tag=tags)
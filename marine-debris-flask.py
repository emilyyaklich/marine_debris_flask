from flask import Flask, request, render_template, abort, flash, get_flashed_messages, redirect, url_for
from werkzeug.utils import secure_filename
import os
import sqlite3
from google import genai
from google.genai import types
from google.api_core.exceptions import ServiceUnavailable
import requests
import base64
import pandas as pd
import tempfile
import time


# code to initialize the database if it does not already exist
def init_db():
    with sqlite3.connect('submissions.db') as con:
        with open('init.sql') as f:
            con.executescript(f.read())

def dbConnection():
    return sqlite3.connect('submissions.db')

# function to insert a database submission
def insert_submission(filepath, category, gps, country):
    with sqlite3.connect('submissions.db') as con:
        con.execute("INSERT INTO submissions (filepath, category, gps, country) VALUES (?, ?, ?, ?)",
            (filepath, category, gps, country)) 

# fetch all of the submissions from the database and return as a pandas dataframe
def fetch_all_submissions():
    with dbConnection() as con:
        df = pd.read_sql("SELECT * FROM submissions", con)
    return df

app = Flask(__name__)

with open("keys.txt", "r") as keys:
    lines = keys.readlines()
# read in this data from the keys.txt file, so it is not directly in the script
app.secret_key = lines[0].strip() # need this to display error messages using flash
google_api_key = lines[1].strip() # need this to access gemini API

@app.route("/submit", methods = ["POST"])

def submit():
    i = request.files.get("image", None)
    gps = request.form.get("gps", None)
    description = request.form.get("description", None)

    # set up access to gemini api (followed instructions from: https://ai.google.dev/gemini-api/docs/image-understanding)
    client = genai.Client(api_key=google_api_key)

    # these are the instructions that I will give to the LLM about my input
    query_instructions = "I want to classify this image as being marine debris or NOT. Keep in mind if debris is washed up on a beach it is still marine debris. I will provide gps coordinates (lat,long), a description, and an image. These are the categories of marine debris it can be: Plastic, Metal, Glass, Rubber, Processed Wood, Fabric, Other. Based on the data I provide, if it is marine debris ONLY say the 'category: description' (if the description is not in English, translate it to English). If it is not marine debris, ONLY say 'ERROR: Not marine debris'"

    if i and gps and description: # only if all 3 data types are provided
        image_bytes = i.read()
        i.seek(0) # my file "i" was saving as empty down below...need to add this line since i.read() sets the cursor at the end
        # set up access to gemini api (followed instructions from: https://ai.google.dev/gemini-api/docs/image-understanding)
        mime_type = i.mimetype
        
        # add a try/except block for accessing the API
        # try 5 times and increase wait time between, otherwise send a message to the use and redirect
        for attempt in range(5):
            try:
                response = client.models.generate_content(model="gemini-2.0-flash",
                contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type,), query_instructions, gps, description],)
                break
            except genai.errors.ServerError as error:
                if "503" in str(error):
                    time.sleep(2 ** attempt)
        else:
            flash("SERVER ERROR: The API model is currently overloaded. Please try submitting later. Thank you!")
            return redirect(url_for("form"))

        if "Not marine debris" in response.text:
            #abort(400, response.text) # don't need this if using flash to show the message
            flash(response.text)
            return redirect(url_for("form"))
        # only if the entry is marine debris should you add it to the database and get country, etc.
        else: 
            os.makedirs("static", exist_ok=True) # need this static folder to render images on an html template
            os.makedirs("static/uploads", exist_ok=True)
            time_stamp = str(int(time.time())) # create a time stamp so if images with the same name are uploaded they won't be overwritten
            filepath = f"uploads/{time_stamp}_{secure_filename(i.filename)}"
            i.save(f"static/{filepath}")
            category = response.text.strip()
            # set up access to nominatim API to get country (online manual; also did this in part one of this lab with /search instead of /reverse)
            base_url = 'https://nominatim.eduoracle.ugavel.com/'
            path = '/reverse'
            lat, lon = gps.split(',')
            params = {'lat':str(lat), 'lon':str(lon), "format":"json"}
            res = requests.get(base_url + path, params)
            api_dict = res.json()
            if "error" in api_dict.keys():
                country = "unable to obtain from coordinates"
            else:
                country = api_dict['address']['country']
            # initialize the database if it does not exist
            if not os.path.exists('submissions.db'):
                init_db()
            insert_submission(filepath, category, gps, country) # add the submission to the database
    else:
        flash("ERROR: All 3 required for submission: Image, GPS, Description")
        return redirect(url_for("form"))
    flash(f"Submission Received! {category}")
    return redirect(url_for("form")) 

@app.route("/", methods = ["GET"])
def form():
    messages = get_flashed_messages() # load any error messages to display
    # only show the database if it exists
    if os.path.exists('submissions.db'): 
        df = fetch_all_submissions()
        html_df = df.to_dict(orient="records")
        return render_template("myform.html", title="Marine Debris", submissions=html_df, messages=messages)
    else:
        return render_template("myform.html", title="Marine Debris", messages=messages)

if __name__ == "__main__":
    app.run(debug=True, host = "0.0.0.0", port=8080)
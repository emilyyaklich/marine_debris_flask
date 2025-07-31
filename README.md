# Marine Debris Flask App
## Devleloped as part of a final project for INFO8000 at the University of Georgia

This flask app will accept submission of a marine debris image, GPS coordinates, and brief description and will query gemini to classify the marine debris into a category (based on the [MDMAP Guide](https://marinedebris.noaa.gov/protocol/mdmap-marine-debris-item-categorization-guide)), add the submission to a SQL database, and project this database onto the app itself.

- `marine-debris-flask.py` contains the flask app
- `templates/` directory contains:
    - `base.html`
    - `myform.html`: this is the form that is displayed and allows for data submission, seeing previous database entries, and error messages
- `init.sql` initializes the database submissions.db if it does not already exist
- `keys.txt.example` supply your own API key and also app.secret_key which is necessary to display messages using flash
    - fill in with your own information and change name to `keys.txt`

I utilized the gemini LLM api (version gemini-2.0-flash) and got a lot of my info/instructions from their online documentation [here](https://ai.google.dev/gemini-api/docs/image-understanding).
It took a bit of testing to could get back exactly what I wanted from the LLM:

- I realized that I had to be specific as possible and limit the output of what what I wanted it to say to a few things, otherwise it liked to be fairly wordy.
- I ended up querying with this message: *"I want to classify this image as being marine debris or NOT. Keep in mind if debris is washed up on a beach it is still marine debris. I will provide gps coordinates (lat,long), a description, and an image. These are the categories of marine debris it can be: Plastic, Metal, Glass, Rubber, Processed Wood, Fabric, Other. Based on the data I provide, if it is marine debris ONLY say the 'category: description' (if the description is not in English, translate it to English). If it is not marine debris, ONLY say 'ERROR: Not marine debris'"* This message was straightforward enough where I specified exactly what I wanted and I am happy with what it ends up returning.


## Key Features
1. If description was given in a different language, translate it to English
2. Before saving the uploaded image, add a time stamp to the front (e.g. `{timestamp}_image.jpg`)
    - I thought adding this would be useful so that if two images with the same name are ever uploaded, they will not be overwritten and each will be stored uniquely
3. If the submission is successfully receieved, print out a message to the screen saying: "Submission Received! category:description" so that the user knows it was successful
4. Contrary, if there are errors, also print them out. These are the errors I accounted for:
    - *ERROR: Not marine debris*. This will be returned if the LLM does not classify the image as marine debris.
    - *ERROR: All 3 required for submission: Image, GPS, Description*. This will be returned if the user does not include all 3 data types in the submission.
    - *SERVER ERROR: The API model is currently overloaded. Please try submitting later. Thank you!*. This will be returned if the LLM api is overloaded (sends a 503 error). With this I also included a try block in my code that will try accessing the api 5 times (increasing the wait time between each successive try) and only send this message if it cannot access the api after that. 
5. I noticed that nominatim cannot return an address (e.g. country) for GPS coordinates that are in the middle of the ocean or not close to land. I do think that adding these entries would still be valuable information to have if I was researching marine debris, so if nominatim cannot classify the coordinates, I still add it to the database, but I just say "unable to obtain from coordinates" in the country variable in the database.
6. The messages returned using flash are in red at the top of the screen, so the user can easily identify them.

### Youtube Video
https://youtu.be/qknBAMuIIco

## Credit 
I would like to thank Dr. Kyle Johnsen for instructing the course and providing helpful feedback on the project.

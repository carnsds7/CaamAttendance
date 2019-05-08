This is the server side of the facial recognition attendance tracker. The server listens for clients.
Then creates a thread for each client to process signing them in or out or recognizing or updating the google sheets specified. 
The ipaddress of the server is specified in the server_config.json file. 
The server also requires a google sheet to update the information to. The filename for
the credentials, database, and spread sheet name must be specified in the json file as well.

The server can either sign a user in or out or create them a recognition data set. The 
data set path must be specified in the server_config.json file as well. This is where
all images of users for the LBPH algorithm to train will be stored. The resulting histogram
filename (which is also specified in the json file) is found in the Recognizer directory.
The server attempts to read (over TCP connection) 20 image arrays found from a client's
during the creation event and then writes those images. When asked to recognize the user,
it reads only one and sends the resulting data of the user with the ID number it guessed.

Data from the users are kept in the specified database file with sqlite 
(as well as most recent activity stored in the google sheet). 
When a client closes the connection, the server updates the
spread sheet for the users that were present during that specific session.

The main method is found in ImageRecognitionServer.py

Run with python3 ImageRecognitionServer.py


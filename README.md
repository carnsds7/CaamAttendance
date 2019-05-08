# CaamAttendance
Prototype Attendance Module for Tutoring Sessions

The clientside code contains a UI for users to signin and out with. It uses
OpenCV to poll for faces through a webcam. It then sends the images to the server
to attempt recognize a user that used the service in the past and set up a
data set (14 images) for recognition. It also sends a signal to server when
closed so that the server may update a spreadsheet (kept on google sheets)
to keep track of user data. 

The four functions of the ui are:
  - Sign users in
  - Sign users out
  - Poll for facial recognition
  - Update Spread sheet upon closing
  
Users are presented with a basic sign in screen on top left of module. There
they will enter there first and last name and course in attendance for. Then
they can just click the signin/out button. They will be signed in or out
and the time recorded for the event on the server side as most attendance works. 

Using OpenCV I wanted to make that process even faster or at least more automated.
Therefore, a user can create a recognition data set by clicking create dataset and
14 images will be captured of there face. Of course the user will verify each one
to help ensure a proper dataset was made. Then, they will be signed in upon a 
successful creation of the data set. The video recording may be seen in the top right
while confirmation images are seen in the bottom right. 

Instructions for use are found in the bottom left. Confirmation text of any event is
found in the box where the action happens.

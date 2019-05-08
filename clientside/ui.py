'''
:Author: Dillon Carns
:Data: 02/08/2019
The UI for the facial recognition/attendance system.
'''
import sys
import threading
from threading import Lock
import time
import numpy as np
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtWidgets import (QApplication, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTextEdit, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QImage, QPixmap, QFont
import cv2
from ClientSide import *

'''
Handles displaying a video feed from opencv
'''
class CamThread(QThread):
    '''
    The CamThread class handles taking in images and querying the server to
    check if a user exits or not
    '''
    changePixmap = pyqtSignal(QImage)
    #flags for operations
    create = False
    cancel = False
    cascPath = "haarcascade_frontalface_default.xml" 
    face_casc = cv2.CascadeClassifier(cascPath)
    busy = False
    submit_wait = False
    tempSocket = None
    img_index = 0
    lock = Lock()
    
    def run(self):
        self.sleep(3)
        cap = cv2.VideoCapture(0)
        while True:
            # read in frame from cam
            ret, frame = cap.read()

            if ret:  # ensure cam is working
                if not UI.bottomRight.isEnabled() and not CamThread.busy:
                    # read image, convert to gray scale
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = CamThread.face_casc.detectMultiScale(gray, 1.3, 5)

                    if len(faces) == 1:
                        # detected a face so lets notify main thread
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        if UI.creating:
                            th = threading.Thread(target=UI.handleCreating, args=(gray, CamThread.img_index))
                            th.daemon = True
                            th.start()
                            print('creating?')
                        else:
                            th = threading.Thread(target=UI.confirmUser, args=(np.array(gray), None))
                            th.daemon = True
                            th.start()
                elif CamThread.busy and UI.creating and UI.readyForImage:
                    # need to update the images here
                    UI.readyForImage = False
                    UI.decision = None
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = CamThread.face_casc.detectMultiScale(gray, 1.3, 5)
                    if len(faces) == 1:
                        th = threading.Thread(target=UI.handleCreating, args=(gray, CamThread.img_index))
                        th.daemon = True
                        th.start()

                cv2.waitKey(64)  # let the image processing relax a little
                # display full frame to provide video feed
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                convertToQtFormat = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
        cap.release()
        cap.destroyAllWindows()

'''
The UI Class handles all of the UI related aspects
'''
class UI(QDialog):
    # private static fields
    _classes = [
            "1100-Discrete Mathematics",
            "1440-Computer Science 1",
            "1445-INTRO TO PROGMG IDS APPLICATIONS",
            "2440-Computer Science 2",
            "2450-Intro to Computer Systems",
            "2490-Intro to Theoretical CS",
            "3100-Junior Seminar",
            "3240-Mobile Programming",
            "3440-Client side Web Programming",
            "3430-Database",
            "3460-Data Structures",
            "3463-Simulation",
            "3481-Computer Systems 1",
            "3482-Computer Systems 2",
            "3490-Programming Languages",
            "3500-Independent Study",
            "3750-Applied Neural Networks",
            "3760-System Admin and Security",
            "3770-Computational Cryptography",
            "3667-Software Engineering",
            "4100-Senior Seminar",
            "4435-Server Side Web Programming",
            "4440-AI",
            "4450-Data Communications and Networking",
            "4465-Computer Graphics",
            "4510-Senior Honors Thesis",
            "4521-Operating Systems",
            "4550-Theoretical Comp Sci",
            "4570-Human Computer Interfaces",
            "4620-Real time Systems",
            "4740-Digital Image Processing",
            "4800-Capstone Project"]
    # public static fields
    first_name = ''
    last_name = ''
    first_name_edit = None
    last_name_edit = None
    course = ''
    UI_course_box = None
    createDataset = False
    bottomRight = None
    topLeft = None
    confirm_txt = None
    update_txt = None
    decision = False
    pictureLabel = None
    readyForImage = False

    # image variables
    _img = None  # an image to display for confirmation
    blank_img = np.zeros((400, 400, 3), np.uint8)

    # FLAGS
    creating = False
    submitting = False

    def __init__(self, width, height, parent=None):

        super(UI, self).__init__(parent)
        self.originalPalette = QApplication.palette()
        mainLabel = QLabel("CA" + u"\u00B2" + "M | Powered by the CS Department.")
        mainLabel2 = QLabel("Please Refer to help notes in bottom left if stuck.")

        mainLabel.setFont(QFont("Times", 14, QFont.Bold))
        mainLabel2.setFont(QFont("Times", 10, QFont.Bold))
        bottomLabel = QLabel('Thank you for using the tutoring sessions!')
        self.width = width
        self.height = height
        
        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()
        self.createBottomLeftWidget()
        self.createBottomRightGroupBox()

        topLayout = QVBoxLayout()
        mainLabel.setAlignment(Qt.AlignCenter)
        mainLabel2.setAlignment(Qt.AlignCenter)
        topLayout.addWidget(mainLabel)
        topLayout.addWidget(mainLabel2)

        mainLayout = QGridLayout()
        mainLayout.addLayout(topLayout, 0, 0, 1, 2)
        UI.topLeft = self.topLeftGroupBox
        mainLayout.addWidget(self.topLeftGroupBox, 1, 0)
        mainLayout.addWidget(self.topRightGroupBox, 1, 1)
        mainLayout.addWidget(self.bottomLeftWidget, 2, 0)
        mainLayout.addWidget(self.bottomRightGroupBox, 2, 1)
        mainLayout.addWidget(bottomLabel, 3, 0)
        UI.bottomRight.setEnabled(False)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setRowStretch(2, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)
        self.setWindowTitle("Facial Recognition Attendance")
        self.setGeometry(0, 0, width, height)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit', 'Are You Sure to Quit?', QMessageBox.No | QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            try:
                updateSpreadSheet()
            except Exception:
                event.accept()
                exit(1)
            event.accept()
        else:
            event.ignore()

    @pyqtSlot(QImage)
    def setVideoImage(self, image):
        self.videoLabel.setPixmap(QPixmap.fromImage(image))

    def createTopLeftGroupBox(self):
        # TODO: Take in user data here!
        # make all the nexessary fields, labels and buttons
        self.topLeftGroupBox = QGroupBox("Submission Area")
        self.topLeftGroupBox.setAlignment(Qt.AlignCenter)
        self.firstNameEdit = QLineEdit('')
        UI.first_name_edit = self.firstNameEdit
        firstNameLabel = QLabel('&First Name:')
        firstNameLabel.setBuddy(self.firstNameEdit)
        self.lastNameEdit = QLineEdit('')
        UI.last_name_edit = self.lastNameEdit
        lastNameLabel = QLabel('&Last Name:')
        lastNameLabel.setBuddy(self.lastNameEdit)
        signin_or_out_label = QLabel('Awaiting use.')
        signin_or_out_label.setStyleSheet("color: rgb(37, 186, 126);")
        signin_or_out_label.setAlignment(Qt.AlignCenter)
        signin_or_out_label.setFont(QFont("Times", 10, QFont.Bold))
        UI.update_txt = signin_or_out_label
        self.courseComboBox = QComboBox()
        coursesLabel = QLabel('&Course:')
        coursesLabel.setBuddy(self.courseComboBox)
        UI.UI_course_box = self.courseComboBox
        self.courseComboBox.addItems(UI._classes)
        submitButton = QPushButton("SIGN IN/OUT")
        submitButton.setDefault(True)
        submitButton.clicked.connect(UI.init_submit)
        createButton = QPushButton("CREATE RECOGNITION SET")
        createButton.setDefault(True)
        createButton.clicked.connect(UI.startCreating)
        clearButton = QPushButton("CLEAR")
        clearButton.setDefault(True)
        clearButton.clicked.connect(self.clearFields)

        # add all fields, labels and buttons to layout group
        layout = QVBoxLayout()
        layout.addWidget(firstNameLabel)
        layout.addWidget(self.firstNameEdit)
        layout.addWidget(lastNameLabel)
        layout.addWidget(self.lastNameEdit)
        layout.addWidget(coursesLabel)
        layout.addWidget(self.courseComboBox)
        layout.addStretch(1)
        layout.addWidget(signin_or_out_label)
        layout.addWidget(submitButton)
        layout.addWidget(createButton)
        layout.addWidget(clearButton)
        layout.addStretch(2)
        self.topLeftGroupBox.setLayout(layout)    

    def clearFields(self):
        UI.setFields('', '', '1100')

    def createTopRightGroupBox(self):
        self.topRightGroupBox = QGroupBox("Video Feed")
        self.topRightGroupBox.setAlignment(Qt.AlignCenter)
        videoWidget = QWidget()
        videoWidget.setGeometry(0, 0, 800, 600)
        self.videoLabel = QLabel(videoWidget)
        self.videoLabel.resize(self.topRightGroupBox.width(), self.topRightGroupBox.height())
        th = CamThread(videoWidget)
        th.changePixmap.connect(self.setVideoImage)
        th.start()
        layout = QHBoxLayout()
        layout.addStretch(2)
        layout.addWidget(videoWidget, 9)
        self.topRightGroupBox.setLayout(layout)

    def createBottomLeftWidget(self):
        self.bottomLeftWidget = QWidget()
        textEdit = QTextEdit()
        textEdit.setPlainText("----------------------------------"
                              "------------HELP NOTES------------"
                              "----------------------------------\n"
                              "1) For standard sign in or out (does both), please type in first name, last name"
                              " and course.\nThen click 'SIGN-IN/OUT' button (top left)"
                              "[you may neglect course when signing out].\n"
                              "2)[optional] To create facial recognition account, enter your first name, last name "
                              "and course then click create recognition set (top left) then please"
                              "confirm the bottom right\nimages and make sure the image of you is clear, the system "
                              "requires 14 images\nand you must confirm each one to ensure a proper user data set"
                              ".\n**Tip: Different angling of the face between photos may help for accuracy.\n"
                              "3) The system automatically polls to see if a user is present in the system\n"
                              "in the bottom right, if it finds user it will ask to confirm and you"
                              "can say yes to auto-fill field info; other wise please manually enter info.\n"
                              "4) Please raise your hand when stuck and require assistance from a tutor.\n"
                              )
        textEdit.selectAll()
        textEdit.setFontPointSize(14)
        textEdit.setReadOnly(True)
        tabelhbox = QHBoxLayout()
        tabelhbox.addWidget(textEdit)
        self.bottomLeftWidget.setLayout(tabelhbox)

    def createBottomRightGroupBox(self):
        self.bottomRightGroupBox = QGroupBox("Confirmation Screen")
        self.bottomRightGroupBox.setAlignment(Qt.AlignCenter)
        UI.bottomRight = self.bottomRightGroupBox
        pictureWidget = QWidget()
        pictureWidget.setGeometry(0, 0, 400, 400)
        UI.pictureLabel = QLabel(pictureWidget)
        # make some options for user
        confirmLabel = QLabel('Awaiting Recognition...')
        confirmLabel.setFont(QFont("Times", 8, QFont.Bold))
        confirmLabel.setGeometry(0, 0, 20, 20)
        UI.confirm_txt = confirmLabel
        UI.setUiImage(UI.blank_img)
        # make buttons responsible for signing users in:
        yesButton = QPushButton("Yes")
        yesButton.setDefault(True)
        yesButton.clicked.connect(UI.setDecisionYES)
        noButton = QPushButton("No")
        noButton.setDefault(True)
        noButton.clicked.connect(UI.setDecisionNO)
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        bottomLayout = QVBoxLayout()
        bottomLayout.setAlignment(Qt.AlignCenter)
        bottomLayout.addWidget(confirmLabel)
        bottomLayout.addWidget(yesButton)
        bottomLayout.addWidget(noButton)

        picLayout = QHBoxLayout()
        picLayout.addStretch(3)
        picLayout.addWidget(pictureWidget, 9)
        midsLayout = QVBoxLayout()
        midsLayout.addLayout(bottomLayout, 1)
        midsLayout.addLayout(picLayout, 3)
        totalLayout = QVBoxLayout()
        totalLayout.setSpacing(8)
        totalLayout.addLayout(midsLayout)
        layout.addItem(totalLayout)
        self.bottomRightGroupBox.setLayout(layout)

    # static methods for manipulating bottom right ui

    def startCreating():
        '''
        sets the creating flag to True.
        :return: n/a
        '''
        f_name = str(UI.first_name_edit.text())
        l_name = str(UI.last_name_edit.text())
        course = UI.UI_course_box.currentText()
        course = course.split('-')[0]
        if '#' not in f_name and '#' not in l_name \
            and 'drop all' not in f_name.lower() \
            and 'drop all' not in l_name.lower() \
            and 'drop all' not in str(l_name.lower() + f_name.lower()) \
            and '*' not in l_name and '*' not in f_name \
            and f_name != '' and l_name != '' and not f_name.isspace() and not l_name.isspace():
            UI.creating = True
            UI.topLeft.setEnabled(False)
            UI.first_name = f_name
            UI.last_name = l_name
            UI.course = course
        else:
            UI.update_txt.setText('Illegal characters in name (or empty) for ' + f_name + ' ' + l_name
                                  + 'can not create a data set with given data.')

    def handleCreating(img, index):
        '''
        This method creates a facial recognition data set for user.
        :return: n/a
        '''
        CamThread.lock.acquire()
        fullName = UI.first_name + ' ' + UI.last_name
        if index > 13:
            UI.update_txt.setText('Data set for : ' + fullName + ' successfully created! ' + fullName + ' is signed in!')
            CamThread.img_index = 0
            CamThread.busy = False
            UI.creating = False
            UI.topLeft.setEnabled(True)
            CamThread.tempSocket = None
            UI.readyForImage = False
            UI.bottomRight.setEnabled(False)
            UI.clearFields()
            CamThread.lock.release()
            return

        course = UI.course
        CamThread.busy = True
        UI.decision = None
        UI.setUiImage(img)
        UI.bottomRight.setEnabled(True)
        endTime = time.time() + 5
        UI.confirm_txt.setText('Confirm Image ' + str(index) + ' for : ' + fullName + '?')
        while UI.decision is None:
            if time.time() >= endTime:
                UI.decision = False
        if UI.decision:
            try:
                if CamThread.tempSocket is not None:
                    ret = CamThread.tempSocket
                    ret = createDataSet(fullName, course, img, index, ret)
                else:
                    ret = createDataSet(fullName, course, img, index, None)
            except Exception:
                UI.confirm_txt.setText('Server issue occurred cancelling.')
                CamThread.busy = False
                UI.creating = False
                UI.topLeft.setEnabled(True)
                CamThread.tempSocket = None
                UI.readyForImage = False
                UI.bottomRight.setEnabled(False)
                CamThread.lock.release()
                return
            if ret != False and ret != 'Done':  # Success and we have the socket for the next image.
                CamThread.tempSocket = ret
                CamThread.img_index += 1

            elif ret == 'Done':  # we finished making this data set.
                CamThread.img_index = 0
                CamThread.busy = False
                CamThread.tempSocket = None
                UI.creating = False
                UI.topLeft.setEnabled(True)
                UI.bottomRight.setEnabled(False)
                UI.readyForImage = False
                CamThread.lock.release()
                return
            else:
                CamThread.busy = False
                UI.creating = False
                UI.topLeft.setEnabled(True)
                CamThread.tempSocket = None
                UI.readyForImage = False
                UI.bottomRight.setEnabled(False)
                CamThread.lock.release()
                return

        UI.readyForImage = True  # let the CameraThread know we're ready for the next
        UI.bottomRight.setEnabled(False)  # disallow extra presses of buttons
        CamThread.lock.release()


    def setUiImage(img):
        '''
        setUiImage method that sets the image to whatever is passed
        :param:img - image to set in the ui for confirmation
        '''
        convertToQtFormat = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_Grayscale8)
        ctq = convertToQtFormat.scaled(QSize(512, 256))
        pixmap = QPixmap(ctq)
        UI.pictureLabel.setPixmap(pixmap)

    def confirmUser(img, p=None):
        '''
        confirmUser - used to recognize a client
        :param img: the image used to send to the server to see who it is
        :param p: does nothing
        :return: n/a
        '''
        CamThread.busy = True
        UI.bottomRight.setEnabled(True)
        UI.decision = None

        UI.setUiImage(img)
        try:
            response = recognizeClient(img)
        except Exception:
            response = False

        endTime = time.time() + 5
        if response != False:
            first, last, course = response.split(' ')
            UI.confirm_txt.setText('Confirm User Info for : ' + first + ' ' + last + '?')
            while UI.decision is None:
                if time.time() >= endTime:
                    UI.decision = False
            if UI.decision:
                UI.first_name_edit.setText(first)
                UI.last_name_edit.setText(last)
                UI.setComboIndex(course)
        else:
            # UI.confirm_txt.setText('Failed to confirm user with server.')
            UI.bottomRight.setEnabled(False)
            while True:
                if time.time() >= endTime - 2:  # let the user see there was an error
                    break

        UI.confirm_txt.setText('Awaiting recognition...')
        UI.setUiImage(UI.blank_img)
        UI.bottomRight.setEnabled(False)
        CamThread.busy = False

    @pyqtSlot()
    def setDecisionNO():
        '''
        Belongs to the no button in bottom right
        sets the current decision to no (False)
        :return: n/a
        '''
        UI.decision = False
    
    @pyqtSlot()
    def setDecisionYES():
        '''
        Belongs to the no button in bottom right
        sets the current decision to yes (True)
        :return: n/a
        '''
        UI.decision = True

    def setComboIndex(text):
        '''
        Sets the combo box current index based on text passed in
        :param: text, text to compare against the combo box data
        :return: the index of the item or default to 0
        '''
        for i in range(len(UI._classes)):
            if text in UI._classes[i]:
                UI.UI_course_box.setCurrentIndex(i)
                return i
        return 0

    def init_submit():
        '''
        starts a thread to sign some one in
        calls UI.submit_action
        :return: n/a
        '''
        UI.topLeft.setEnabled(False)
        th = threading.Thread(target=UI.submit_action)
        th.daemon = True
        th.start()

    def submit_action():
        '''
        this will take the fields and sign in or our the user
        As long as the name is valid
        :return: n/a
        '''
        f_name = str(UI.first_name_edit.text())
        l_name = str(UI.last_name_edit.text())
        course = UI.UI_course_box.currentText()
        course = course.split('-')[0]
        if '#' not in f_name and '#' not in l_name \
            and 'drop all' not in f_name.lower() \
            and 'drop all' not in l_name.lower() \
            and 'drop all' not in str(l_name.lower() + f_name.lower()) \
            and '*' not in l_name and '*' not in f_name \
            and f_name != '' and l_name != '' and not f_name.isspace() and not l_name.isspace():
            try:
                response = signInorOutUser(f_name, l_name, course)
            except Exception as e:
                response = 'BAD'
            if response == 'SIN':
                UI.update_txt.setText('User ' + f_name + ' ' + l_name + ' signed in!')
            elif response == 'SNO':
                UI.update_txt.setText('User ' + f_name + ' ' + l_name + ' signed out!')
            else:
                UI.update_txt.setText('Error occurred while signing user in/out.')
        else:
            UI.update_txt.setText('Illegal characters used in name or empty for ' + f_name + ' ' + l_name)
        UI.setFields('', '', '1100')  # reset the fields
        UI.topLeft.setEnabled(True)  # allow next user to sign in or out

    def setFields(f_name, l_name, c_num):
        '''
        Static method.
        Sets the submission area data that is visible to user.
        :param f_name: first name to be changed in the text edit of submission area
        :param l_name: last name to be changed in the text edit of submission area
        :param c_num: course number to be set in submission area
        :return:
        '''
        UI.first_name_edit.setText(f_name)
        UI.last_name_edit.setText(l_name)
        course = str(c_num)
        UI.setComboIndex(course)

def main():
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    size = screen.size()
    ui = UI(size.width(), size.height())
    ui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

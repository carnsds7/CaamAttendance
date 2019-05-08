'''
@author Dillon Carns
@version 04/09/2019
'''
import socket
import pickle
import json
from time import sleep

HOST = ''
PORT = 0

def createDataSet(fullName, course, gray, sampleNum, clientSocket):
    '''
    Will tell server that new user is being added
    :param clientSocket: maintains socket at current ip
    '''
    if clientSocket is None:
        clientSocket = initialize()

    if sampleNum == 0:
        try:
            user_info = "create" + fullName + '#' + course
            clientSocket.send(user_info.encode())
        except Exception:
            return False
    # while True:
    # img is in color, but need grayscale image to function
    # send grayscale frame to server for face extraction
    dataToSend = pickle.dumps(gray)
    try:
        sleep(0.1)
        clientSocket.send(dataToSend)
    except Exception as e:
        return False
    try:
        clientSocket.recv(1)
    except Exception:
        return False
    if sampleNum > 13:
        clientSocket.close()
        return "DONE"
    return clientSocket



def signInorOutUser(firstname, lastname, course):
    '''
    responsible for signing in user
    :param clientSocket: socket to send data on
    :param firstname: firstname of user from ui
    :param lastname: last name of user from ui
    :param course: course of user from ui
    '''
    user_info = 'signin' + str(firstname) + ' ' + str(lastname) + '#' + str(course)
    clientSocket = initialize()
    try:
        clientSocket.send(user_info.encode())
    except Exception:
        raise Exception
    response = clientSocket.recv(8).decode()
    clientSocket.close()
    return response

def updateSpreadSheet():
    '''
    Lets the server know that the client side is closing
    For me, the server updates a spread sheet
    '''
    clientSocket = initialize()
    try:
        clientSocket.send('sysend'.encode())
    except Exception:
        raise Exception
    clientSocket.close()

def recognizeClient(gray):
    '''
    Responsible for sending a grayscale picture (provided by ui or other) to server for recognition
    and attendance to then be recorded
    :param gray: image in grayscale to be sent
    :return: The data to use or False on failure
    '''
    clientSocket = initialize()
    try:
        clientSocket.send('recognize'.encode())
    except Exception as e:
        print('exception occurred: ' + e)
        raise Exception
    # send the serialized image data to server
    data = pickle.dumps(gray)
    clientSocket.send(data)
    sleep(.1)
    response = None
    # while response == None:
    try:
        # receive the data from server
        response = clientSocket.recv(512).decode()
    except Exception as e:
        print(e)
        response = 'NO'
    clientSocket.close()
    if response[:3] == "YES":
        return response[3:]
    else:
        return False

def getFreePort():
    '''
    Gets a free port on client machine
    currently unused.
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sock.bind(('', 0))
    sock.listen(socket.SOMAXCONN)
    ipaddr, port = sock.getsockname()
    sock.close();
    return str(port)

def initialize():
    '''
    Responsible for setting up a new client connection
    :return: clientSocket or None if connection fails
    '''
    try:
        with open('client_config.json') as f:
            client_conf = json.load(f)
    except Exception:
        return None
    HOST = client_conf["HOST"]
    PORT = int(client_conf["PORT"])

    try:
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.connect((HOST, PORT))
        clientSocket.settimeout(5)
    except Exception:
        return None

    return clientSocket


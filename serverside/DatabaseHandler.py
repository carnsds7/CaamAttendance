'''
@author Dillon Carns
@version 08/30/2018
'''
import sqlite3
import random

def getProfile(id, db_name):
    '''
    Retrieves profile of user from database
    :param id: id of user, int
    :param db_name: name of database file
    :return: profile
    '''
    conn = sqlite3.connect(db_name)
    cmd = "SELECT * from Students WHERE ID=\"" + str(id) + "\""
    cursor = conn.execute(cmd)
    profile = None
    for row in cursor:
        profile = row
    conn.close()
    return profile

def getProfileWithName(name, db_name):
    '''
    Retrieves id of user from name
    :param name: name of user
    :param db_name: name of database file
    :return: profile
    '''
    conn = sqlite3.connect(db_name)
    cmd = "SELECT * from Students WHERE Name=\"" + str(name) + "\""
    cursor = conn.execute(cmd)
    profile = None
    for row in cursor:
        profile = row
    conn.close()
    return profile


def generateID(db_name):
    '''
    Generates a random user ID that's not in use
    :param db_name: name of database file
    :return: id: a new user id number
    '''
    id = 7777
    conn = sqlite3.connect(db_name)
    conn.row_factory = lambda cursor, row: row[0]
    c = conn.cursor()
    ids = c.execute('SELECT ID FROM Students').fetchall()
    for i in ids:
        if id == i:
            id = random.randint(1000, 10000) #allows for 10000 users - increase seconde param for more
    conn.close()
    return id


def insertOrUpdate(ID, name, db_name):
    '''
    Either inserts or updates a user's data depending
    :param ID: id of user to insert or update
    :param name: name of user
    :param db_name: name of database file
    '''
    conn = sqlite3.connect(db_name)
    cmd = "SELECT * FROM Students WHERE ID=" + "\"" + str(ID) + "\";"
    cursor = conn.execute(cmd)
    ifExists = 0
    for row in cursor:
        ifExists = 1
    if (ifExists == 1):
        cmd = "UPDATE Students SET Name=" + str(name) + " WHERE ID=\"" + str(ID) + "\";"
    else:
        cmd = "INSERT INTO Students(ID,Name) VALUES(\"" + str(ID) + "\",\"" + str(name) + "\");"
    conn.execute(cmd)
    conn.commit()
    conn.close()
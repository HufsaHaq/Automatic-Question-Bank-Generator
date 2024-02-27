#WITHIPRO_SQLITE.PY

import sqlite3
import os
import base64
import fitz
from images_extraction import *  # Import the extract_images function
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

DB_NAME = 'withipro_database.db'

# Function to extract metadata from a PDF
def extract_pdf_metadata(pdf_file_path):
    try:
        # Open the PDF file
        with open(pdf_file_path, 'rb') as pdf_file:
            parser = PDFParser(pdf_file)
            doc = PDFDocument(parser)

            # Check if doc.info is a list
            if isinstance(doc.info, list):
                # Assuming the relevant information is in the first dictionary in the list
                info_dict = doc.info[0]
            else:
                info_dict = doc.info

            # Extract metadata fields
            metadata = {
                "year": info_dict.get('SeriesYear', b'').decode('utf-8'),
                "subject": info_dict.get('Subject', b'').decode('utf-8'),
                "level": info_dict.get('QualFacet', b'').decode('utf-8'),
                "exam_code": info_dict.get('Component', b'').decode('utf-8'),
                "exam_board": info_dict.get('Author', b'').decode('utf-8'),
                "paper_number": info_dict.get("CompFacet", b'').decode('utf-8').split()[-1]
            }

            # Assign None to fields that don't exist in metadata
            for key in ["year", "subject", "level", "exam_code", "exam_board", "paper_number"]:
                metadata[key] = metadata.get(key, None)

            return metadata
    except Exception as e:
        print("Error extracting metadata:", e)
        return {}

def delete_database():
    
    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    cursor.execute('''DROP TABLE IF EXISTS users;''')
    cursor.execute('''DROP TABLE IF EXISTS metadata;''')
    cursor.execute('''DROP TABLE IF EXISTS questions;''')
    cursor.execute('''DROP TABLE IF EXISTS answers;''')
    print("Tables deleted")

    #save the database
    db.commit()  

    #dis-connect from the database
    db.close()

def create_database():
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Create the user table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL, 
            is_teacher BOOLEAN
        );''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            pdf_id INTEGER PRIMARY KEY,
            year TEXT,
            subject TEXT,
            level TEXT,
            exam_code TEXT,
            exam_board TEXT,  
            regex_pattern TEXT,
            paper_number TEXT,
            type TEXT
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY,
            pdf_id INTEGER,
            question_image TEXT,
            question_text TEXT,
            question_number TEXT,
            usage_count INTEGER DEFAULT 0,
            is_hidden INTEGER DEFAULT 0,  -- 0 for False, 1 for True
            FOREIGN KEY (pdf_id) REFERENCES metadata (pdf_id)
        );
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS answers (
            answer_id INTEGER PRIMARY KEY,
            pdf_id INTEGER,
            answer_image TEXT,
            answer_text TEXT,
            question_number TEXT,
            FOREIGN KEY (pdf_id) REFERENCES metadata (pdf_id)
        );
        ''')

        # Create the count table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS count (
            pdf_count INTEGER
        );
        ''')
        cursor.execute('INSERT OR IGNORE INTO count (pdf_count) VALUES (0);')

        # Save changes and close the database
        conn.commit()
        conn.close()

        print("Database and tables created successfully")
    except sqlite3.Error as e:
        print("Error:", e)


def populate_database():
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Sample data for users table 
        users_data = [
            ("user1", "password1", 0),
            ("admin1", "password3", 1),
            ("admin2", "password4", 1),
            ("teacher1", "password2", 1)
        ]

        # Insert sample data into the users table
        cursor.executemany('''
        INSERT INTO users (username, password, is_teacher)
        VALUES (?, ?, ?);
        ''', users_data)

        # Commit changes and close the database connection
        conn.commit()
        conn.close()

        print("Database populated successfully")
    except sqlite3.Error as e:
        print("Error:", e)

def show_all():

    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    # show the entries in the users table
    print("USERS TABLE")
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    for i in results:
        print(i)

    print("METADATA TABLE")
    cursor.execute("SELECT * FROM metadata")
    results = cursor.fetchall()
    for i in results:
        print(i)

    print("QUESTIONS TABLE")
    cursor.execute("SELECT * FROM questions")
    results = cursor.fetchall()
    for i in results:
        print(i)

    print("ANSWERS TABLE")
    cursor.execute("SELECT * FROM answers")
    results = cursor.fetchall()
    for i in results:
        print(i)

    #dis-connect from the database
    db.close()

    return results

##################################################################################################
##################################################################################################

def showmeall():
    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    # show the entries in the users table
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()

    #dis-connect from the database
    db.close()

    return results

def adminadduser(username, password1, password2, is_teacher):
    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    mycommand = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(mycommand, (username,))
    results = cursor.fetchall()

    # dis-connect from the database
    db.close()

    if results != []:
        return ["Error", "Username already exists"]
    elif password1 != password2:
        return ["Error", "Passwords do not match"]
    else:
        # connect to the database
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        # Set is_teacher to 1 if the user is a teacher, 0 otherwise
        mycommand = 'INSERT INTO users (username, password, is_teacher) VALUES (?, ?, ?)'
        cursor.execute(mycommand, (username, password1, is_teacher))

        # save the database
        db.commit()

        # dis-connect from the database
        db.close()
        return ["Created user: ", username]

def adminupdateuser(username, password1, password2):
    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    mycommand = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(mycommand, (username,))
    results = cursor.fetchall()

    # dis-connect from the database
    db.close()

    if results == []:
        return ["Error", "Username does not exist"]
    elif password1 != password2:
        return ["Error", "Passwords do not match"]
    else:
        # connect to the database
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        mycommand = 'UPDATE users SET password = ? WHERE username = ?'
        cursor.execute(mycommand, (password1, username,))

        # save the database
        db.commit()

        # dis-connect from the database
        db.close()
        return ["Updated username: ", username]

def admindeleteuser(username):
    # connect to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()

    mycommand = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(mycommand, (username,))
    results = cursor.fetchall()

    # dis-connect from the database
    db.close()

    if results == []:
        return ["Error", "Username does not exist"]
    else:
        # connect to the database
        db = sqlite3.connect(DB_NAME)
        cursor = db.cursor()

        mycommand = 'DELETE FROM users WHERE username = ?'
        cursor.execute(mycommand, (username,))

        # save the database
        db.commit()

        # dis-connect from the database
        db.close()
        return ["Deleted user : ", username]
    

    
##################################################################################################
##################################################################################################

if __name__ == '__main__':
    # Call the function to delete the database
    #delete_database()
    
    # Call the function to create the database and tables
    #create_database()

    # Call the function to populate the database
    #populate_database()

    # Call the function to display contents of the database
    show_all()
    
    print("please use app")

    
    



        

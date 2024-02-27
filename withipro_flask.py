#WITHIPRO_FLASK.PY
from flask import Flask, render_template, redirect, request, url_for, session
from functools import wraps
import sqlite3
import os
import base64
import fitz
from images_extraction import *
from withipro_sqlite import *
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = 'your_secret_key_here'

# SQLite Database Configuration
DB_NAME = 'withipro_database.db'

# Configure the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads'

#Routes################################################################################################################################################
#######################################################################################################################################################
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Initialize error variable

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username is 'admin1' or 'admin2'
        if username == 'admin1' or username == 'admin2':
            session['logged_in'] = True
            return redirect(url_for('home'))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['regex_pattern'] = ""
            session['pdf_filename'] = ""
            session['user_id'] = user[0]
            session['is_teacher'] = user[3]
            session['logged_in'] = True
            return redirect(url_for('index', message=f"Welcome {username}"))
        else:
            error = "Invalid username or password"  # Set error message

    return render_template('login.html', error=error)

@app.route('/')
@login_required
def index():
    if 'user_id' in session:
        is_teacher = session['is_teacher']
        if is_teacher:
            return redirect(url_for('teacher_home'))
        else:
            return redirect(url_for('student_home'))
    return "Welcome to your Withipro."

@app.route('/teacher_home', methods=['GET', 'POST'])
@login_required
def teacher_home():
    if 'user_id' in session and session['is_teacher']:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Select question papers without corresponding markschemes
        cursor.execute("""
            SELECT q.year, q.subject, q.level, q.exam_board, q.exam_code
            FROM metadata q
            LEFT JOIN metadata a ON q.year = a.year 
                                AND q.subject = a.subject 
                                AND q.level = a.level 
                                AND q.exam_board = a.exam_board 
                                AND q.exam_code = a.exam_code
                                AND a.type = 'MS'
            WHERE q.type = 'QP'
              AND a.year IS NULL;  -- Exclude cases where both QP and MS exist
        """)

        question_papers_without_markschemes = cursor.fetchall()

        # Select markschemes without corresponding question papers
        cursor.execute("""
            SELECT a.year, a.subject, a.level, a.exam_board, a.exam_code
            FROM metadata a
            LEFT JOIN metadata q ON a.year = q.year 
                                AND a.subject = q.subject 
                                AND a.level = q.level 
                                AND a.exam_board = q.exam_board 
                                AND a.exam_code = q.exam_code
                                AND q.type = 'QP'
            WHERE a.type = 'MS'
              AND q.year IS NULL;  -- Exclude cases where both QP and MS exist
        """)

        markschemes_without_question_papers = cursor.fetchall()

        # Need to return two separate lists
        markschemes = question_papers_without_markschemes
        question_papers = markschemes_without_question_papers
        print(question_papers)
        print(markschemes)

        conn.close()

        if request.method == 'POST':
            if 'search' in request.form:
                return redirect(url_for('search'))
            elif 'upload_pdf' in request.form:
                return redirect(url_for('upload_question_paper'))
            elif 'question_analytics' in request.form:
                return redirect(url_for('question_analytics'))
            elif 'delete_pdf' in request.form:
                return redirect(url_for('delete_pdf'))

        # Pass todo_list to the template
        return render_template('teacher_home.html', 
                       question_papers=question_papers,
                       markschemes=markschemes)

    else:
        return redirect(url_for('login'))


    
@app.route('/student_home')
@login_required
def student_home():
    if 'user_id' in session and not session['is_teacher']:
        if request.method == 'POST':
            if 'search' in request.form:
                return redirect(url_for('search'))
            elif 'question_analytics' in request.form:
                return redirect(url_for('question_analytics'))
        return render_template('student_home.html')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('index'))

#########################################################################################################################################################################
#########################################################################################################################################################################

@app.route('/upload_pdf', methods=['GET', 'POST'])
@login_required
def upload_pdf():
    mymessage = ""
    type_existing = ""
    text_from_pages = []
    pdf_filename = None

    if 'user_id' in session and session['is_teacher']:
        if request.method == 'POST':
            pdf = request.files['pdf_file']

            if pdf:
                pdf_filename = secure_filename(pdf.filename)

                # Save the uploaded file to the specified folder
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf.filename))

                pdf.save(pdf_path)

                try:
                    doc = fitz.open(pdf_path)
                    for page_num in range(min(10, doc.page_count)):
                        page_text = doc[page_num].get_text()
                        page_with_number = f'Page {page_num + 1}:\n\n{page_text}'  
                        text_from_pages.append(page_with_number)
                    doc.close()

                    # Store the filename in the session as a relative path
                    session['pdf_filename'] = pdf_path
                    print("pdf_path:", pdf_path)

                    # Check if regex_pattern is provided
                    regex_pattern = request.form.get('regex_pattern')
                    session['regex_pattern'] = regex_pattern
                    print("regex_pattern:", regex_pattern)

                    # Check which button was pressed
                    button_pressed = request.form.get('button_pressed')

                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    
                    metadata = extract_pdf_metadata(pdf_path)   
                    year = metadata.get('year', "")
                    subject = metadata.get('subject', "")
                    level = metadata.get('level', "")
                    exam_code = metadata.get('exam_code', "")
                    exam_board = metadata.get('exam_board', "")
                    paper_number = metadata.get('paper_number', "")

                    existing_metadata = cursor.execute('''SELECT type FROM metadata 
                                      WHERE year = ? AND subject = ? AND level = ? 
                                      AND exam_code = ? AND exam_board = ? 
                                      AND regex_pattern = ? AND paper_number = ?;''',
                                   (year, subject, level, exam_code, exam_board, regex_pattern, paper_number)).fetchone()

                    if existing_metadata:
                        type_existing = existing_metadata[0]

                    if button_pressed == 'Text':
                        # Render the pdf_text.html template
                        return render_template('pdf_text.html', message=mymessage, text_from_pages=text_from_pages, pdf_filename=pdf_filename)

                    elif button_pressed == 'Experiment':
                        # Redirect to the /experiment_regex route
                        return redirect(url_for('experiment_regex'))

                    elif button_pressed == 'Submit':
                        if regex_pattern:
                            # Redirect to the /show_images route
                            return redirect(url_for('show_images'))
                        else:
                            mymessage = "Please enter a regex pattern before submitting."

                except Exception as e:
                    mymessage = "Error extracting text from PDF: " + str(e)

            else:
                mymessage = "No file selected for text extraction"

        return render_template('upload_pdf.html', type_existing=type_existing, message=mymessage, text_from_pages=text_from_pages, pdf_filename=pdf_filename)

    return redirect(url_for('login'))

@app.route('/experiment_regex', methods=['GET', 'POST'])
@login_required
def experiment_regex():
    pdf_file = session.get('pdf_filename')
    pattern_images = []
    regex_pattern=""

    if pdf_file and request.method == 'POST':
        # Get the regex pattern entered by the user
        regex_pattern = request.form.get('regex_pattern')

        if regex_pattern:
            try:
                # Extract images for the current pattern
                questions = extract_images_from_pdf(regex_pattern, pdf_file)

                if questions:
                    # Take the first 30 question's images for the current pattern
                    for question in questions[:30]:
                        pattern_images.append(question[1])
            except Exception as e:
                # Handle exceptions (e.g., invalid PDF, regex pattern)
                print(f"Error extracting images: {e}")

    return render_template('experiment_regex.html', example_images=pattern_images ,regex_pattern=regex_pattern)

#########################################################################################################################################################################
#########################################################################################################################################################################
@app.route('/show_images', methods=['GET', 'POST'])
@login_required
def show_images():
    regex_pattern = session.get('regex_pattern')
    pdf_file = session.get('pdf_filename')
    images = []

    metadata = extract_pdf_metadata(pdf_file) 
    
    if pdf_file and regex_pattern:
        clips = extract_images_from_pdf(regex_pattern, pdf_file)

        if clips and len(clips) > 0:
            for i in range(len(clips)):
                images.append(clips[i][1])

    if request.method == 'POST':
        button_pressed = request.form.get('button_pressed')
        
        if button_pressed == 'Save':
            return redirect(url_for('save_images'))

    # Pass metadata values to the template
    return render_template('show_images.html', regex_pattern=regex_pattern, images=images,
                           metadata=metadata)

@app.route('/save_images', methods=['POST'])
@login_required
def save_images():
    regex_pattern = session.get('regex_pattern')
    pdf_file = session.get('pdf_filename')
    image_type = request.form.get('image_type')  
    question_numbers = request.form.getlist('question_number')
    # Correctly retrieve metadata from form fields
    year = request.form.get('metadata_year')
    subject = request.form.get('metadata_subject')
    level = request.form.get('metadata_level')
    exam_code = request.form.get('metadata_exam_code')
    exam_board = request.form.get('metadata_exam_board')
    paper_number = request.form.get('metadata_paper_number')

    if pdf_file and regex_pattern:
        images_and_text = extract_images_from_pdf(regex_pattern, pdf_file)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        text = []
        images = []

        for item in images_and_text:
            text.append(item[0])
            images.append(item[1])

        # Check if metadata with the same details and regex_pattern_qus already exists
        cursor.execute('''SELECT pdf_id FROM metadata 
                          WHERE year = ? AND subject = ? AND level = ? 
                          AND exam_code = ? AND exam_board = ? 
                          AND regex_pattern = ? AND paper_number = ?;''',
                       (year, subject, level, exam_code, exam_board, regex_pattern, paper_number))

        existing_pdf_id = cursor.fetchone()

        if existing_pdf_id:
            # Metadata with the same details and regex_pattern_qus already exists
            return redirect(url_for('upload_pdf'))

        # Metadata does not exist, proceed with inserting new metadata
        cursor.execute('UPDATE count SET pdf_count = pdf_count + 1;')
        cursor.execute('SELECT pdf_count FROM count;')
        x = cursor.fetchone()[0]

        if image_type == 'Questions':
            cursor.execute('''INSERT INTO metadata (pdf_id, year, subject, level, exam_code, exam_board, regex_pattern, paper_number, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'QP');''', (x, year, subject, level, exam_code, exam_board, regex_pattern, paper_number))
            for i, question_number in enumerate(question_numbers):
                image_data = images_and_text[i][1]
                cursor.execute('''INSERT INTO questions (pdf_id, question_image, question_text, question_number) VALUES (?, ?, ?, ?);''', (x, image_data, text[i], question_number))
        elif image_type == 'Answers':
            cursor.execute('''INSERT INTO metadata (pdf_id, year, subject, level, exam_code, exam_board, regex_pattern, paper_number, type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MS');''', (x, year, subject, level, exam_code, exam_board, regex_pattern, paper_number))
            for i, question_number in enumerate(question_numbers):
                image_data = images_and_text[i][1]
                cursor.execute('''INSERT INTO answers (pdf_id, answer_image, answer_text, question_number) VALUES (?, ?, ?, ?);''', (x, image_data, text[i], question_number))

        # Delete records with question_number as "0" from both questions and answers tables
        cursor.execute('''DELETE FROM questions WHERE question_number = "0";''')
        cursor.execute('''DELETE FROM answers WHERE question_number = "0";''')

        conn.commit()
        conn.close()
        try:
            os.remove(pdf_file)
        except Exception as e:
            print(f"Error removing file: {e}")
        mymessage = 'Images and metadata have been saved successfully!'

        return redirect(url_for('search'))

    return redirect(url_for('login'))
#########################################################################################################################################################################
#########################################################################################################################################################################

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    results = []  # Initialize results to an empty list
    pdf_id_values = []

    if request.method == 'POST':
        year = request.form.get('year', '*')
        
        # Extract selected exam boards from form data
        selected_exam_boards = [request.form.get('examboard_AQA', None),
                                request.form.get('examboard_CCEA', None),
                                request.form.get('examboard_Edexcel', None),
                                request.form.get('examboard_OCR', None),
                                request.form.get('examboard_WJEC', None)]

        level = request.form.get('level', '*')
        subject = request.form.get('subject', '*')
        paper_number = request.form.get('paper_number', '*')
        
        # Extract keywords from form data
        keywords = request.form.get('keywords', '*')
        additional_keywords = request.form.get('additional_keywords', '*')
        more_keywords = request.form.get('more_keywords', '*')


        is_teacher = session.get('is_teacher')
        query = "SELECT pdf_id FROM metadata WHERE 1 = 1 "

        query_params = []

        # Modify the conditions to exclude empty strings
        if year and year != '*':
            query += " AND year = ?"
            query_params.append(year)
        if level and level != '*':
            query += " AND level = ?"
            query_params.append(level)
        if subject and subject != '*':
            query += " AND subject = ?"
            query_params.append(subject)
        if paper_number and paper_number != '*':
            query += " AND paper_number = ?"
            query_params.append(paper_number)
        if any(selected_exam_boards):
                selected_exam_boards_conditions = []
                for exam_board in selected_exam_boards:
                    selected_exam_boards_conditions.append("exam_board = ?")
                    query_params.append(exam_board)
                
                if selected_exam_boards_conditions:
                    query += " AND (" + " OR ".join(selected_exam_boards_conditions) + ")"

        
        print("SQL Query:", query)
        print("Query Params:", query_params)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query, query_params)
        pdf_ids = cursor.fetchall()
        print("pdf ids :", pdf_ids)
        conn.close()
        query_params2 = []

        # Fetch relevant questions using obtained pdf_ids
        if pdf_ids:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Generate placeholders for pdf_ids
            placeholders = ','.join('?' * len(pdf_ids))

            # Modify the query to use the placeholders
            is_teacher = session.get('is_teacher')
            if is_teacher:
                query = f"SELECT question_image, question_number, pdf_id , is_hidden FROM questions WHERE pdf_id IN ({placeholders})"  #don't exclude hidden questions
            else:
                query = f"SELECT question_image, question_number, pdf_id FROM questions WHERE pdf_id IN ({placeholders}) AND is_hidden = 0"  # Exclude hidden questions

            # Extract the first element of each tuple in pdf_ids
            for id_ in pdf_ids:
                pdf_id_values.append(id_[0])

            # Extend query_params2 with the elements of pdf_id_values
            query_params2.extend(pdf_id_values)

            # Initialize keyword_conditions
            keyword_conditions = []

            if keywords != '*':
                keywords_list = keywords.split()
                for keyword in keywords_list:
                    keyword_conditions.append("LOWER(question_text) LIKE LOWER(?)")
                    query_params2.append(f"%{keyword.lower()}%")

            if additional_keywords != '*':
                additional_keywords_list = additional_keywords.split()
                for keyword in additional_keywords_list:
                    keyword_conditions.append("LOWER(question_text) LIKE LOWER(?)")
                    query_params2.append(f"%{keyword.lower()}%")

            if more_keywords != '*':
                more_keywords_list = more_keywords.split()
                for keyword in more_keywords_list:
                    keyword_conditions.append("LOWER(question_text) LIKE LOWER(?)")
                    query_params2.append(f"%{keyword.lower()}%")

            if keyword_conditions:
                query += " AND (" + " OR ".join(keyword_conditions) + ")"

            print("SQL Query:", query)
            print("Query Params:", query_params2)

            cursor.execute(query, query_params2)
            results = cursor.fetchall()
            conn.close()

    return render_template('search.html', results=results)

@app.route('/compile', methods=['POST'])
@login_required
def compile():
    selected_ids = []
    question_numbers = []
    q_images = []
    a_images = []
    answer_ids = []
    action = request.form.get('action')

    is_teacher = session.get('is_teacher')

    mymessage = ""

    if action in ['Questions', 'Answers']:
        # iterate over the form data
        for i in range(len(request.form)):
            checkbox = request.form.get('checkbox' + str(i))
            selected_id = request.form.get('selected_questions_' + str(i))
            question_number = request.form.get('question_number_' + str(i))

            if checkbox == 'on':
                selected_ids.append(selected_id)
                question_numbers.append(question_number)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        for i in range(len(selected_ids)):
            # need the first two characters of the selected question number to identify other parts
            prefix = question_numbers[i][:2]
            print(prefix)

            # Modify the query to fetch only non-hidden questions
            cursor.execute("SELECT question_image, usage_count  FROM questions WHERE pdf_id = ? AND question_number LIKE ? AND is_hidden = 0", (selected_ids[i], f'{prefix}%'))
            question_data = cursor.fetchall()

            # Check if question_data is not empty before attempting to access it
            if question_data:
                for row in question_data:
                    q_images.append(row[0])  # Assuming the image is stored in the first column
                    updated_usage_count = row[1] + 1
                    cursor.execute("UPDATE questions SET usage_count = ? WHERE pdf_id = ? AND question_number LIKE ?", (updated_usage_count, selected_ids[i], f'{prefix}%'))

            else:
                print(f"No non-hidden question images found for pdf_id {selected_ids[i]}")


            # fetch metadata for the question
            cursor.execute("SELECT * FROM metadata WHERE pdf_id = ?", (selected_ids[i],))
            metadata_data = cursor.fetchone()

            # Check if metadata_data is empty
            if not metadata_data:
                print(f"Metadata not found for pdf_id {selected_ids[i]}")
                continue  # Skip to the next iteration

            # Use metadata to find the answer PDF IDs
            cursor.execute("""
                    SELECT pdf_id FROM metadata
                    WHERE year = ? AND subject = ? AND level = ? AND exam_board = ? AND paper_number = ? AND pdf_id != ?  
                """, (metadata_data[1], metadata_data[2], metadata_data[3], metadata_data[5], metadata_data[7], selected_ids[i]))

            result = cursor.fetchall()
            for row in result:
                answer_ids.append(row[0])

            print(f"answer_ids for pdf_id {selected_ids[i]}: {answer_ids}")

            if answer_ids:
                for pdf_id in answer_ids:
                    cursor.execute("SELECT answer_image FROM answers WHERE pdf_id = ? AND question_number LIKE ?", (pdf_id, f'{prefix}%'))
                    answer_data = cursor.fetchall()
                    for row in answer_data:
                        a_images.append(row[0])                
        conn.commit()
        conn.close()
        unique_q_images = list(set(q_images))  # Remove duplicates
        unique_a_images = list(set(a_images))  # Remove duplicates

        if action == 'Questions':
            return render_template('questions.html', q_images=unique_q_images)
        elif action == 'Answers':
            return render_template('answers.html', a_images=unique_a_images)

    
    elif action == 'Update Hidden Status' and is_teacher:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        for i in range(len(request.form)):
            checkbox = request.form.get('checkbox' + str(i))
            selected_question = request.form.get('selected_questions_' + str(i))
            question_number = request.form.get('question_number_' + str(i))
            hidden_value = request.form.get('hidden' + str(i))  # Retrieve the hidden radio button value

            if checkbox == 'on':
                # Update the is_hidden status in the database based on the radio button value
                cursor.execute("UPDATE questions SET is_hidden = ? WHERE pdf_id = ? AND question_number = ?", (int(hidden_value), selected_question, question_number))

        conn.commit()
        conn.close()

        mymessage = "Selected questions have been updated."
        return redirect(url_for('search', message=mymessage))

#########################################################################################################################################################################
#########################################################################################################################################################################
@app.route('/delete_pdf', methods=['GET', 'POST'])
@login_required
def delete_pdf():
    message = None  # Initialize message variable
    if request.method == 'POST':
        # Get user input
        year = request.form.get('year')
        subject = request.form.get('subject')
        level = request.form.get('level')
        exam_code = request.form.get('exam_code')
        exam_board = request.form.get('exam_board')
        paper_number = request.form.get('paper_number')

        # Validate that all fields are filled
        if not year or not subject or not level or not exam_code or not exam_board or not paper_number:
            message = 'Please fill in all fields.'
        else:
            # Create a connection to the database
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # Check if the PDF exists in the database
            cursor.execute("""
                SELECT pdf_id FROM metadata
                WHERE year = ? AND subject = ? AND level = ? AND exam_code = ? AND exam_board = ? AND paper_number = ?
            """, (year, subject, level, exam_code, exam_board, paper_number))

            pdf_ids = cursor.fetchall()

            if not pdf_ids:
                message = 'No matching records found.'
            else:
                # Delete the PDF and its associated questions
                for pdf_id in pdf_ids:
                    # Delete questions associated with the PDF
                    cursor.execute("DELETE FROM questions WHERE pdf_id = ?", (pdf_id[0],))

                    # Delete answers associated with the PDF
                    cursor.execute("DELETE FROM answers WHERE pdf_id = ?", (pdf_id[0],))

                    # Delete metadata and related PDFs
                    cursor.execute("DELETE FROM metadata WHERE pdf_id = ?", (pdf_id[0],))

                    # Delete the PDF file from the server
                    pdf_path = os.path.join('uploads', f'{pdf_id[0]}.pdf')

                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)

                # Commit changes and close the connection
                conn.commit()
                conn.close()
                message = 'Selected exam papers successfully deleted.'

    return render_template('delete_pdf.html', message=message)


#########################################################################################################################################################################
#########################################################################################################################################################################

@app.route('/question_analytics')
@login_required
def question_analytics():
    if 'user_id' in session:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT question_image, usage_count
        FROM questions
        ORDER BY usage_count DESC
        LIMIT 10;
        ''')

        analytics_data = cursor.fetchall()
        conn.close()

        return render_template('question_analytics.html', analytics_data=analytics_data)

    return redirect(url_for('login'))

#########################################################################################################################################################################
#########################################################################################################################################################################
@app.route('/home')
@login_required
def home():
   # Add logic to retrieve or generate the message
   message = "Welcome to the home page!"

   # Render the home.html template and pass the message variable
   return render_template('home.html', message=message)

@app.route('/adminshowusers', methods=['GET','POST'])
@login_required
def admin_show_users():
   results = showmeall()
   return render_template('adminshowusers.html',rows=results)

@app.route('/adminadduser', methods=['GET', 'POST'])
@login_required
def admin_add_user():
   mymessage = "Enter username and password to add"

   if request.method == 'POST':
      myname = request.form['username']
      mypassword1 = request.form['password1']
      mypassword2 = request.form['password2']
      is_teacher = request.form.get('is_teacher')  # Check if the checkbox is checked

      # Convert is_teacher to 1 if checked, else 0
      if is_teacher == "1":
          is_teacher = 1
      else:
          is_teacher = 0
          
      results = adminadduser(myname, mypassword1, mypassword2, is_teacher)

      if results[0] == "Error":
         mymessage = results[0] + results[1]
      else:
         mymessage = results[0] + results[1]
         return render_template('home.html', message=mymessage)
   return render_template('adminadduser.html', message=mymessage)


@app.route('/adminupdateuser', methods=['GET', 'POST'])
@login_required
def admin_update_user():

   mymessage = "Enter username and password to update"

   if request.method == 'POST':
      myname = request.form['username']
      mypassword1 = request.form['password1']
      mypassword2 = request.form['password2']

      results = adminupdateuser(myname, mypassword1, mypassword2, )

      if results[0] == "Error":
         mymessage = results[0] + results[1]
      else:
         mymessage = results[0] + results[1]
         return render_template('home.html', message=mymessage)
   return render_template('adminupdateuser.html',message=mymessage)
   
@app.route('/admindeleteuser', methods=['GET', 'POST'])
@login_required
def admin_delete_user():

   mymessage = "Enter username to delete"

   if request.method == 'POST':
      myname = request.form['username']

      results = admindeleteuser(myname, )

      if results[0] == "Error":
         mymessage = results[0] + results[1]
      else:
         mymessage = results[0] + results[1]
         return render_template('home.html', message=mymessage)

   return render_template('admindeleteuser.html',message=mymessage)

#########################################################################################################################################################################
#########################################################################################################################################################################

if __name__ == '__main__':
    app.run(debug=True)



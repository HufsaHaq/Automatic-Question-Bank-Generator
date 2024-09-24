# NEA
2023-24 A-level AQA Computer Science NEA Coursework Project

This project accepts a pdf input and uses regex to break the question paper into individual question part sthat are stored in a database and can be selected and compiled to form topical papers / mock exams etc.

Objectives
1) User Interface (UI):
i) Design a user-friendly interface for students, admins and teachers.
ii) Implement user authentication to distinguish between students and teachers.
iii) Create a page that displays the top 10 used questions
iv) Add buttons that will redirect the user to the correct feature: search, delete pdf,
upload pdf and question analytics.
v) Limit the access that students have to certain features.
vi) Integrate features for admin users.
2) PDF Processing:
i) Implement a function that accepts the PDF file path and regex pattern and extracts
images and text of individual questions and returns this as a list.
ii) This will use fitz (PyMuPDF) and IRect.
iii) The data structure used for storing question information in the provided code is a
list of lists. Each inner list will contain two elements:
(1) The question text (extracted from the PDF).
(2) The question image, represented as a base64-encoded string.
iv) Implement logic to identify if the next image is a part of the previous question.
v) Implement skip and stop phrases to decrease processing time by skipping certain
pages in a pdf.
3) User Uploading:
i) Include a page of extracted text from the first ten page of the pdf to allow the user
to form the regex pattern.
ii) Include a page that will allow the user to enter a regex pattern and see example
images to allow the user to refine their regex pattern.
iii) Include a page that will allow the user to enter the question numbers and approve
the metadata of the PDF
4) Database Design:
i) Design a database to store the extracted question information, along with the
question image.
ii) Design a function to extract the subject, level, years, exam board and exam code by
analysing the metadata of the pdf using PDFMiner library.
iii) Create a metadata table to represent the subject, level, years, exam board and exam
code with the pdf id.
iv) Add a function that encrypts the image in base64.
v) Design tables to store the question and mark scheme details, including the text,
image, question number, pdf id and question id and a flag to see if the question is
hidden.
vi) Design table to store user details.
5) Database Integration:
i) Connect the application to a suitable database system (SQLite).
ii) Implement functions to insert the exam paper details and question details into the
database.
iii) Implement logic to update the hidden status of questions by teachers.
6) Retrieving and Displaying Questions:
i) Implement a search feature to retrieve questions based on various criteria like
subject, topic, year, and exam board.
ii) Write a generalised database queries to fetch questions and their associated
information from the database.
Computer Science 7517D Page 56 of 166
Hufsa Haq - 2287 Withington Girls School - 32449
iii) Display the retrieved questions to the user.
iv) Ensure that students can only view non-hidden questions.
v) Add checkboxes to allow the user to select the questions they want to compile.
vi) Add radios to show the hidden status of each question.
7) User Management (Admin):
i) Allow admin users to add new users with appropriate permissions.
ii) Enable admin users to delete existing users from the system.
iii) Implement the ability for admin users to update user information.
iv) Provide a feature for admin users to view the list of all users in the system.
8) Additional Features:
i) Add a to do list which displays question papers that have mark scheme that are yet
to be uploaded and vice versa.
ii) Implement file validation to ensure that only PDF files, the standard format for
exam papers, are accepted

# NEA  
2023-24 A-level AQA Computer Science NEA Coursework Project  

My project processes PDF exam papers using regex to extract individual questions, storing them in a database. These questions can then be selected and compiled to create custom topical papers, mock exams, or other assessments.

## Objectives  

### 1) User Interface (UI):
- Design a user-friendly interface for students, admins, and teachers.
- Implement user authentication to distinguish between students and teachers.
- Create a page that displays the top 10 used questions.
- Add buttons to redirect the user to the correct features: search, delete PDF, upload PDF, and question analytics.
- Limit student access to certain features.
- Integrate features for admin users.

### 2) PDF Processing:
- Implement a function that accepts the PDF file path and regex pattern, extracts images and text of individual questions, and returns them as a list.
  - This will use `fitz` (PyMuPDF) and `IRect`.
- The data structure for storing question information is a list of lists. Each inner list contains two elements:
  1. The question text (extracted from the PDF).
  2. The question image, represented as a base64-encoded string.
- Implement logic to identify if the next image is part of the previous question.
- Implement skip and stop phrases to reduce processing time by skipping certain pages in a PDF.

### 3) User Uploading:
- Include a page displaying the extracted text from the first ten pages of the PDF to help the user form the regex pattern.
- Include a page where the user can enter a regex pattern and view example images to refine the pattern.
- Provide a page for users to enter question numbers and approve the metadata of the PDF.

### 4) Database Design:
- Design a database to store the extracted question information, along with question images.
- Implement a function to extract subject, level, years, exam board, and exam code by analyzing PDF metadata using `PDFMiner`.
- Create a metadata table to represent subject, level, years, exam board, and exam code with the PDF ID.
- Implement encryption for the image in base64 format.
- Design tables to store the question and mark scheme details, including text, image, question number, PDF ID, question ID, and a flag for hidden questions.
- Design a table to store user details.

### 5) Database Integration:
- Connect the application to a suitable database system (e.g., SQLite).
- Implement functions to insert exam paper and question details into the database.
- Implement logic to update the hidden status of questions by teachers.

### 6) Retrieving and Displaying Questions:
- Implement a search feature to retrieve questions based on various criteria like subject, topic, year, and exam board.
- Write generalized database queries to fetch questions and associated information.
- Display retrieved questions to the user.
- Ensure students can only view non-hidden questions.
- Add checkboxes for users to select questions for compilation.
- Add radio buttons to show the hidden status of each question.

### 7) User Management (Admin):
- Allow admin users to add new users with appropriate permissions.
- Enable admin users to delete users from the system.
- Implement the ability for admin users to update user information.
- Provide a feature for admin users to view all users in the system.

### 8) Additional Features:
- Add a to-do list showing question papers that still need mark schemes and vice versa.
- Implement file validation to accept only PDF files, which are the standard format for exam papers.


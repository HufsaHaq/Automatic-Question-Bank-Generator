#IMAGE_EXTRACTION.PY
import fitz
import re
import base64
from PIL import Image
import io

# Function to convert an image to base64 encoding
def image_to_base64(image):
    try:
        # Convert the Pixmap to bytes
        img = image.tobytes(output='jpg', jpg_quality=100)

        # Convert the image to base64 encoding only if the image is not empty
        if img:
            image = Image.open(io.BytesIO(img))
            im_file = io.BytesIO()
            image.save(im_file, format="JPEG")
            im_bytes = im_file.getvalue()  # im_bytes: image in binary format.
            im_b64 = base64.b64encode(im_bytes).decode("utf-8")
            return im_b64
    except Exception as e:
        print(f"Error converting image to base64: {e}")
    return None

def extract_images_from_pdf(regex_pattern, pdf_file_path):
    doc = fitz.open(pdf_file_path)
    questions = []  # 2D list to store question information

    prev_clip = None  # To keep track of the previous question's clip

    # Phrases that, if found in the page text, will cause the page to be skipped
    skip_phrases = ["There are no questions printed on this page", "For this paper you must have",
                    "Level of response mark schemes are broken down into levels",
                    "Examiners are required to assign each of the candidate’s responses to the most appropriate level",
                    "Mark schemes are prepared by the ","Please check the examination details below before entering your candidate information"]

    # Phrases that, if found in the page text, will cause the program to stop
    stop_phrases = ["END OF QUESTIONS", "Additional page"]

    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        page_text = page.get_text()
        coordinates = []

        # Check if any skip phrases are present in the page text
        if any(phrase in page_text for phrase in skip_phrases):
            print(f"Skipping page {page_num + 1}.")
            continue  # Skip this page and move to the next one

        # Check if any stop phrases are present in the page text
        if any(phrase in page_text for phrase in stop_phrases):
            print(f"Found stop phrase on page {page_num + 1}. Stopping program.")
            break  # Stop the program

        # Find all instances of the regex pattern and store the matches in a list
        question_matches = re.findall(regex_pattern, page_text)

        # Find the coordinates of the matches using page.search_for
        for match in question_matches:
            rects = page.search_for(match.replace('\n', ' '))
            for rect in rects:
                coordinates.append(rect.y0)

        coordinates = list(set(coordinates))  # This deletes the duplicates in the list
        coordinates.sort()  # Ensures the list is in ascending order

        # Check if the first item in coordinates is greater than 150 and insert 50 in front of it
        if coordinates and coordinates[0] > 150:
            coordinates.insert(0, 50)

        # Append 830 to the end of the coordinates list when len(coordinates) > 1
        if len(coordinates) > 0:
            coordinates.append(830)

        for i in range(len(coordinates) - 1):
            start_idx = int(coordinates[i])
            end_idx = int(coordinates[i + 1])

            # Extract the question text and handle Unicode errors
            question_text = page_text[start_idx:end_idx].encode('utf-8', 'ignore').decode('utf-8')

            # Create a Fitz Rect object to clip the area between coordinates
            clip_rect = fitz.Rect(0, start_idx, page.rect.width, end_idx)

            # Save the question image with clipping
            img = page.get_pixmap(clip=clip_rect)

            # Convert the image to base64 encoding
            image = image_to_base64(img)

            # Append the question information to the 2D list
            if image is not None:
                questions.append([question_text, image])

            prev_clip = clip_rect  # Update the previous question's clip

    return questions

if __name__ == "__main__":
    print('use the app file')

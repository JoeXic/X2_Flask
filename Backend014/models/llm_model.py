import os

def ask_llm(text_input, image_filepath):
    # Extract the name of the image file from the filepath
    image_filename = os.path.basename(image_filepath)

    # Concatenate the text_input with the image filename
    result = f"{text_input} {image_filename}"

    return result

import os
import io
import sys
import fnmatch
import json
import base64
from PIL import Image, ImageDraw, ImageOps

def image_to_bytes(image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=image.format)
    return imgByteArr.getvalue()

def image_to_base64(image):
    return base64.b64encode(image_to_bytes(image)).decode('utf-8')

def base64_to_image(image_base64):
    return Image.open(io.BytesIO(base64.b64decode(image_base64.encode('utf-8'))))

def get_position_size(position):
    return (position["sirka"], position["vyska"])

def get_position_left_top(position):
    return (position["zleva"], position["zhora"])

def get_position_rectangle(position):
    top = position["zhora"]
    left = position["zleva"]
    bottom = top + position["vyska"]
    right = left + position["sirka"]
    return [(left, top), (right, bottom)]

def get_template(template_name):
    with open("./config/vzory.json", "r", encoding="utf-8") as f:
        vzory = json.load(f)
    for item in vzory["vzory"]:
        if item["nazev"] == template_name:
            return item
    return False

def get_position(template_name, position_name):
    template = get_template(template_name)
    if not template:
        return False
    for pos_item in template["pozice"]:
        if pos_item["nazev"] == position_name:
            return pos_item
    return False

def put_image_on_position(template, position, image_to_paste):
    #open template photo
    img_template = Image.open(template["soubor"])
    #open image, convert to grayscale and set size for position
    img_obrazek = image_to_paste.convert("L").resize(get_position_size(position))
    #inverted image
    img_obrazek_inverted = ImageOps.invert(img_obrazek)
    #mask with alpha
    img_maska = img_obrazek_inverted.copy()
    img_maska.putalpha(img_obrazek_inverted)
    #paste template with image, applying mask
    if (template["negativ"]=="ne"):
        img_template.paste(img_obrazek, get_position_left_top(position), mask=img_maska)
    else:
        img_template.paste(img_obrazek_inverted, get_position_left_top(position), mask=img_maska)
    #return result
    return img_template

def put_position_outline(template, position):
    #open template photo
    img_template = Image.open(template["soubor"])
    #draw position outline
    draw = ImageDraw.Draw(img_template)
    draw.rectangle(get_position_rectangle(position), outline="red")
    #return result
    return img_template

def paste_image_on_position(template_name, position_name, image_base64):
    #get and check template and position
    template = get_template(template_name)
    position = get_position(template_name, position_name)
    if not template or not position:
        return False

    #decode image to paste
    image_to_paste = base64_to_image(image_base64)

    #paste
    image = put_image_on_position(template, position, image_to_paste)

    #return encoded
    return image_to_base64(image)

def show_position_on_template(template_name, position_name):
    #get and check template and position
    template = get_template(template_name)
    position = get_position(template_name, position_name)
    if not template or not position:
        return False

    #show position
    image = put_position_outline(template, position)

    #return encoded
    return image_to_base64(image)

def test_paste(template_name, position_name, image_path):

    with open(image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read())

    result_base64 = paste_image_on_position(template_name, position_name, image_base64)
    image = base64_to_image(result_base64)
    image.show()

def test_show(template_name, position_name):
    image_base64 = show_position_on_template(template_name, position_name)
    image = base64_to_image(image_base64)
    image.show()


#TEST
#test_paste("Bílé tričko dámské", "Levé prso", "./pics/srdicko.jpg")
#test_show("Bílé tričko dámské", "Levé prso")
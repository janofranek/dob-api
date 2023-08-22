import os
import io
import sys
import fnmatch
import json
import base64
import urllib.request
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
    return (int(position["width"]), int(position["height"]))

def get_position_left_top(position):
    return (int(position["left"]), int(position["top"]))

def get_position_rectangle(position):
    top = int(position["top"])
    left = int(position["left"])
    bottom = top + int(position["height"])
    right = left + int(position["width"])
    return [(left, top), (right, bottom)]

def get_template(config_data, template_name):
    for item in config_data["templates"]:
        if item["templateName"] == template_name:
            return item
    return False

def get_position(config_data, template_name, position_name):
    template = get_template(config_data, template_name)
    if not template:
        return False
    for pos_item in template["positions"]:
        if pos_item["positionName"] == position_name:
            return pos_item
    return False

def put_image_on_position(template, position, image_to_paste):
    #open template photo
    file_name = "template_image.jpg"
    urllib.request.urlretrieve(template["imageUrl"], file_name)
    img_template = Image.open(file_name)
    os.remove(file_name)
    #open image, convert to grayscale and set size for position
    img_obrazek = image_to_paste.convert("L").resize(get_position_size(position))
    #inverted image
    img_obrazek_inverted = ImageOps.invert(img_obrazek)
    #mask with alpha
    img_maska = img_obrazek_inverted.copy()
    img_maska.putalpha(img_obrazek_inverted)
    #paste template with image, applying mask
    if (template["negative"]):
        img_template.paste(img_obrazek_inverted, get_position_left_top(position), mask=img_maska)
    else:
        img_template.paste(img_obrazek, get_position_left_top(position), mask=img_maska)
    #return result
    return img_template

def put_position_outline(template, position):
    #open template photo
    file_name = "template_image.jpg"
    urllib.request.urlretrieve(template["imageUrl"], file_name)
    img_template = Image.open(file_name)
    os.remove(file_name)
    #draw position outline
    draw = ImageDraw.Draw(img_template, "RGBA")
    draw.rectangle(get_position_rectangle(position), fill=(255,164,0,127))
    draw.rectangle(get_position_rectangle(position), outline=(255,164,0,255), width=3)
    #return result
    return img_template

def paste_image_on_position(config_data, template_name, position_name, image_base64):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template_name, position_name)
    if not template or not position:
        return False

    #decode image to paste
    image_to_paste = base64_to_image(image_base64)

    #paste
    image = put_image_on_position(template, position, image_to_paste)

    #return encoded
    return image_to_base64(image)

def show_position_on_template(config_data, template_name, position_name):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template_name, position_name)
    if not template or not position:
        return False

    #show position
    image = put_position_outline(template, position)

    #return encoded
    return image_to_base64(image)

def test_paste(config_data, template_name, position_name, image_path):

    with open(image_path, "rb") as img_file:
        image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

    result_base64 = paste_image_on_position(config_data, template_name, position_name, image_base64)
    image = base64_to_image(result_base64)
    image.show()

def test_show(config_data, template_name, position_name):
    image_base64 = show_position_on_template(config_data, template_name, position_name)
    image = base64_to_image(image_base64)
    image.show()



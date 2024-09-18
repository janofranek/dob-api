import os
import io
import sys
import fnmatch
import json
import base64
import requests
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

def get_design(config_data, design_name):
    for item in config_data["designs"]:
        if item["designName"] == design_name:
            return item
    return False

def get_position_def(config_data, position_name):
    for item in config_data["positions"]:
        if item["positionName"] == position_name:
            return item
    return False

def fill_in_height(config_data, position_name, position):
    position_def = get_position_def(config_data, position_name)
    height = 0
    if not position_def:
        height = position["width"]
    elif not (position_def["arWidth"] or position_def["arWidth"]==0):
        height = position["width"]
    else:
        height = position["width"] / position_def["arWidth"] * position_def["arHeight"]
    position["height"] = height
    return position

def get_position(config_data, template, position_name):
    if not template:
        return False
    for pos_item in template["positions"]:
        if pos_item["positionName"] == position_name:
            return fill_in_height( config_data, position_name, pos_item )
    return False

def put_image_on_position(template, position, design):
    #open template photo
    response = requests.get(template["imageUrl"])
    img_template = Image.open(io.BytesIO(response.content))
    #open design, convert to grayscale and set size for position
    response = requests.get(design["imageUrl"])
    img_design = Image.open(io.BytesIO(response.content)).convert("L").resize(get_position_size(position))
    #inverted image
    img_design_inverted = ImageOps.invert(img_design)
    #mask with alpha
    img_mask = img_design_inverted.copy()
    img_mask.putalpha(img_design_inverted)
    #paste template with design, applying mask
    img_template.paste(img_design, get_position_left_top(position), mask=img_mask)
    #return result
    return img_template

def put_position_outline(template, position):
    #open template photo
    response = requests.get(template["imageUrl"])
    img_template = Image.open(io.BytesIO(response.content))
    #draw position outline
    draw = ImageDraw.Draw(img_template, "RGBA")
    draw.rectangle(get_position_rectangle(position), fill=(255,164,0,127))
    draw.rectangle(get_position_rectangle(position), outline=(255,164,0,255), width=3)
    #return result
    return img_template

def paste_image_on_position(config_data, template_name, position_name, design_name):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template, position_name)
    design = get_design(config_data, design_name)
    if not template or not position or not design:
        return False
    #paste
    image = put_image_on_position(template, position, design)
    #return encoded
    return image_to_base64(image)

def show_position_on_template(config_data, template_name, position_name):
    #get and check template and position
    template = get_template(config_data, template_name)
    position = get_position(config_data, template, position_name)
    if not template or not position:
        return False
    #show position
    image = put_position_outline(template, position)
    #return encoded
    return image_to_base64(image)



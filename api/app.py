# -*- encoding:utf-8 -*-

from flask import Flask, send_file
from PIL import Image
from os.path import dirname, abspath, join
import io
from .drawHandleArk import (
    single_image_handle,
    ten_image_handle,
    hundred_image_handle,
    ten_draw,
    get_mongolia
)

app = Flask(__name__)
dir = dirname(abspath(__file__))

@app.route("/arknights/arknightsdraw", methods=['POST', 'GET'])
def arknights():
    img = ten_draw()
    file_object = io.BytesIO()
    img.save(file_object, 'PNG')
    file_object.seek(0)
    return send_file(file_object, mimetype='image/PNG')


@app.route('/',methods=['POST', 'GET'])
def arknights_draw():
    img = Image.open(join(dir, '..', 'docs', 'main.png'))
    file_object = io.BytesIO()
    img.save(file_object, 'png')
    file_object.seek(0)
    return send_file(file_object, mimetype='image/png')



if __name__ == "__main__":
    app.run(debug=True)
    print("servers start")

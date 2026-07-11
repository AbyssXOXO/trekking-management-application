import os
import secrets
from PIL import Image
from . import app

def save_picture(form_picture): #for getting the ext and file name for pfp
    random_hex = secrets.token_hex(16)
    _, f_ext = os.path.splitext(form_picture.filename)
    pfp_fn = random_hex + f_ext 
    pfp_path = os.path.join(app.root_path, 'static/profile_pics', pfp_fn)

    output_size = (120, 120)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(pfp_path)

    return pfp_fn #to return the name to be saved in db

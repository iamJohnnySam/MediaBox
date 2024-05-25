from PIL import Image

from shared_tools.logger import log


def resize_image(job_id: int, picture_location):
    foo = Image.open(picture_location)
    w, h = foo.size
    if w > h and w > 1024:
        foo = foo.resize((1024, int(h * 1024 / w)))
    elif h > w and h > 1024:
        foo = foo.resize((int(w * 1024 / h), 1024))

    foo.save(picture_location, optimize=True, quality=95)
    log(job_id=job_id, msg=f'Received Photo > {picture_location}, File size > {foo.size}')

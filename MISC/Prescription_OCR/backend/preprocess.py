import cv2
import numpy as np
from PIL import Image
import io

def preprocess_image(image_bytes):

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    img = np.array(image)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray,(5,5),0)

    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    return img
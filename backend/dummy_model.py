import random

def predict(image_path):
    disease = random.choice(["Pneumonia", "Normal", "COVID-19"])
    confidence = round(random.uniform(0.80, 0.99), 2)  # must be FLOAT
    return disease, confidence

import numpy as np
from preprocess import preprocess_image
from tensorflow.keras.models import load_model

# Load the model from the file
model = load_model('best_model.h5')
labels = ['Good', 'Moderate', 'Unhealthy', 'Unhealthy (Sensitive)', 'Very Unhealthy']

def predict_from_image(img_path):
    image_data = preprocess_image(image_path=img_path)
    prediction = model.predict(image_data)
    predicted_index = np.argmax(prediction)
    predicted_label = labels[predicted_index]
    return predicted_label 

from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash, session
import os
import rasterio
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename
from extraction import extract_pollution_data
from model import predict_from_image


app=Flask(__name__)
app.secret_key='flask_app_pollution_classification_V3'

UPLOAD_FOLDER=os.path.join("static","uploads")
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

REPORT_FOLDER=os.path.join("static","reports")
app.config['REPORT_FOLDER']=REPORT_FOLDER

os.makedirs(UPLOAD_FOLDER,exist_ok=True)
os.makedirs(REPORT_FOLDER,exist_ok=True)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/go_home')
def go_home():
    image_path = session.get('image_path')

    # If there's no image path in session, just go home
    if not image_path:
        return redirect(url_for('home'))

    # Move the current image to archive
    if os.path.exists(image_path):
        archive_folder = os.path.join("static", "archive")
        os.makedirs(archive_folder, exist_ok=True)

        filename = os.path.basename(image_path)
        archived_path = os.path.join(archive_folder, filename)

        if os.path.exists(archived_path):
            os.remove(archived_path)

        os.rename(image_path, archived_path)

    # Delete report image if exists
    report_image_path = os.path.join(app.config['REPORT_FOLDER'], 'report_image.png')
    if os.path.exists(report_image_path):
        os.remove(report_image_path)

    # Clear session and go home
    session.clear()
    return redirect(url_for('home'))



@app.route('/predict', methods=['POST'])
def predict():
    location = request.form.get('location')
    image = request.files.get('image')

    if image and image.filename.lower().endswith(('.tif', '.tiff')):
        filename=secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)
        result=predict_from_image(image_path)
        session['label']=result
        session['image_path']=image_path
        session['file_name']=filename
        return redirect(url_for('report'))
    elif location:
        extracted_path =extract_pollution_data(location,app.config['UPLOAD_FOLDER'])
        if os.path.exists(extracted_path):
            result = predict_from_image(extracted_path)
            session['label'] = result
            session['image_path'] = extracted_path
            session['file_name'] = os.path.basename(extracted_path)
            return redirect(url_for('report'))
        else:
            flash("Pollution image could not be generated. Please try a different location.")
            return redirect(url_for('home'))         
    
    else:
      flash("Invalid file type. Please upload a GeoTIFF image.")
      return redirect(url_for('home'))


@app.route('/report')
def report():


    label = session.get('label')
    image_path = session.get('image_path')
    filename = session.get('file_name')

    if not all([label, image_path, filename]):
        return "Required data missing from session", 400

    # Using rasterio to read the image and display its channels
    with rasterio.open(image_path) as src:
        bands = src.read([1, 2, 3, 4])  # Reading the bands (4 channels)

    pollutants = ['NO₂ (mol/m²)', 'SO₂ (mol/m²)', 'O₃ (mol/m²)', 'CO (mol/m²)']
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    for i in range(4):
        img = axes[i].imshow(bands[i], cmap='inferno')
        axes[i].set_title(pollutants[i])
        axes[i].axis('off')
        cbar = plt.colorbar(img, ax=axes[i], fraction=0.046, pad=0.04)
        cbar.set_label('Concentration')


    # Save the report as an image (optional, you could also save a PDF or text file)
    report_image_path = os.path.join(app.config['REPORT_FOLDER'], 'report_image.png')
    plt.savefig(report_image_path,transparent=True)
    plt.close()

    # Provide information about the label
    label_info = {
        'Good': 'Air quality is considered satisfactory, and air pollution poses little or no risk.',
        'Moderate': 'Air quality is acceptable; however, some pollutants may be a concern for people who are highly sensitive to air pollution.',
        'Unhealthy': 'Health alert: everyone may experience health effects. Sensitive groups may experience more serious effects.',
        'Unhealthy (Sensitive)': 'Health warning for sensitive groups. Everyone else should stay alert.',
        'Very Unhealthy': 'Health emergency. The entire population is likely to be affected.'
    }

    info = label_info.get(label, 'No information available for this label.')

    return render_template('report.html',label=label,label_info=info, report_image_path=report_image_path,image_path=image_path, image_name=filename )


@app.route('/about')
def about():
    return render_template('about.html')
# @app.route('/download_report')
# def download_report():
#     # Allow the user to download the report image
#     report_image_path = os.path.join(app.config['REPORT_FOLDER'], 'report_image.png')
#     return send_from_directory(directory=app.config['REPORT_FOLDER'], filename='report_image.png')
    

if __name__== "__main__":
    app.run(debug=True)

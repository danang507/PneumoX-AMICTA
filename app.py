from flask import Flask, redirect, url_for, render_template, request, session,jsonify
from werkzeug.utils import secure_filename
from gevent.pywsgi import WSGIServer
import numpy as np
from PIL import Image
from flask_mysqldb import MySQL

# Keras
from keras.applications.imagenet_utils import preprocess_input, decode_predictions
from keras.models import load_model
from keras.preprocessing import image
from keras.preprocessing.image import load_img
from keras.preprocessing.image import img_to_array

import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'sfksdfksfldskfl sldfsdlfdslk'



# memanggil model
MODEL_PATH = 'models/model_deteksi_pneumonia.h5'
model = load_model(MODEL_PATH)

# Koneksi ke database
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'pneumox'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


# Halaman utama
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard')) 

    return render_template('index.html')

#menerima inputan dari form login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Ambil data dari form
        username = request.form['username']
        password = request.form['password']

        #koneksi ke database dan mencari username dan password yang sama seperti diinputkan
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone() 

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            # Jika username atau password tidak cocok maka akan menampilkan keterangan
            return render_template('index.html')

    return render_template('index.html')

#mengarahkan ke halaman dasboard
@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')

    else:
        return render_template('index.html')

#mengarahkan ke halaman dasboard
@app.route('/dashboardoutput')
def dashboardoutput():
    if 'username' in session:
        # Membuat kursor untuk mengambil data dari database
        cursor = mysql.connection.cursor()
        # Lakukan kueri SQL untuk mengambil data dari database
        cursor.execute("SELECT * FROM pasien")
        data = cursor.fetchall()
        # Menutup kursor setelah selesai mengambil data
        # Render template HTML dan kirim data ke template
        cursor.close()
        return render_template('dashboarddata.html', value=data)

    else:
        return render_template('index.html')


#jika ingin logout
@app.route('/logout', methods=['POST','GET'])
def logout():
    # Hapus session 'username'
    session.pop('username', None)
    return render_template('index.html')


#memasukkan data ke database dan melakukan prediksi pada gambar x-ray
@app.route('/predict', methods=['GET','POST'])
def predict():
     if request.method == 'POST':
        # Ambil data dari form
        namapasien = request.form['namapasien']
        identitas = request.form['identitas']
        usia = request.form['usia']
        jeniskelamin = request.form['jeniskelamin']
        
        #memprediksi gambar dari form
        imagefile= request.files['imagefile']
        image_path = "./uploads/" + imagefile.filename
        imagefile.save(image_path)

        img = image.load_img(image_path, target_size=(150,150))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)

        images = np.vstack([x])
        classes = model.predict(images, batch_size=32)
        prediksi = np.argmax(classes)

        #menentukan hasil prediksi berupa normal atau pneumonia
        if prediksi == 0:
            classification = 'normal'
        else:
            classification = 'pneumonia'

        diagnosa = classification

        #mengkoneksikan ke database
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO pasien (nama_pasien, no_identitas,umur_pasien, jenis_kelamin, diagnosa) VALUES (%s, %s,%s,%s,%s)", (namapasien,identitas,usia,jeniskelamin,diagnosa))
        mysql.connection.commit()
        cursor.close()

        return render_template('dashboard.html')  

@app.route('/statistic')
def statistic():
    if 'username' in session:
        cursor = mysql.connection.cursor()
         # Query untuk menghitung jumlah pasien dengan diagnosa pneumonia
        cursor.execute("SELECT COUNT(*) as total FROM pasien WHERE diagnosa = 'pneumonia'")
        result_pneumonia = cursor.fetchone()
        count_pneumonia = result_pneumonia['total'] if result_pneumonia and 'total' in result_pneumonia else 0

        # Query untuk menghitung jumlah pasien dengan diagnosa normal
        cursor.execute("SELECT COUNT(*) as total FROM pasien WHERE diagnosa = 'normal'")
        result_normal = cursor.fetchone()
        count_normal = result_normal['total'] if result_normal and 'total' in result_normal else 0
        
        labels = ['Pneumonia', 'Normal']
        values = [count_pneumonia, count_normal]
        colors = ['red', 'green']

        if all(value == 0 for value in values):
            plot_url = None
        
        else:
            # Buat plot Pie Chart
            fig1, ax1 = plt.subplots(figsize=(6, 4))
            ax1.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')  # Biar pasti pie chart berbentuk lingkaran

            # Tambahkan legenda
            ax1.legend(loc="best", labels=['{} - {}'.format(i, j) for i, j in zip(labels, values)])

            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)

            plot_url = base64.b64encode(img.getvalue()).decode()


        #total pasien
        cursor.execute("SELECT COUNT(*) as total_pasien FROM pasien")
        total_pasien = cursor.fetchone()['total_pasien']
        cursor.close()
        
        return render_template('statistic.html',total_pasien = total_pasien, plot_url = plot_url)


    else:
        return render_template('index.html')

@app.route('/delete/<int:id_pasien>', methods=['POST'])
def delete(id_pasien):
    if 'username' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM pasien WHERE id_pasien = %s", (id_pasien,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboardoutput'))

@app.route('/update', methods= ['POST', 'GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        identitas = request.form['identitas']
        usia = request.form['usia']
        jenis_kelamin = request.form['jenis_kelamin']
        


        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE pasien SET nama_pasien=%s, no_identitas=%s, umur_pasien=%s, jenis_kelamin=%s WHERE id_pasien=%s", (name, identitas, usia, jenis_kelamin , id_data))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('dashboardoutput'))

if __name__ == "__main__":
    app.run()

  

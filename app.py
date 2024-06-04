from flask import Flask, redirect, url_for, render_template, request, session
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
        cursor.execute("INSERT INTO pasien (nama_pasien, umur_pasien, jenis_kelamin, diagnosa) VALUES (%s, %s,%s,%s)", (namapasien,usia,jeniskelamin,diagnosa))
        mysql.connection.commit()
        cursor.close()

        return render_template('dashboard.html')  

if __name__ == "__main__":
    app.run()

  

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import joblib
import mysql.connector


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = 'your-secret-key'  # Kunci rahasia untuk sesi


model = joblib.load('model_rf_coba.sav')


# Koneksi ke database MySQL
conn = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='',
    database='tugas_akhir'
)


class Dokter:
    def __init__(self, nama_dokter, gender_dokter, spesialis):
        self.nama_dokter = nama_dokter
        self.gender_dokter = gender_dokter
        ## self.harga = harga
        self.spesialis = spesialis


@app.route('/')
def home():
    uname_user = session.get('uname_user')
    return render_template("index.html", uname_user=uname_user)


@app.route('/rekomendasi')
def rekomendasi():
    if 'uname_user' in session:
        return render_template("rekomendasi.html")
    else:
        return redirect(url_for('login'))


@app.route('/rekomendasi', methods=['POST'])
def hasil():
    # Check session for authentication
    if 'uname_user' not in session:
        return redirect(url_for('login'))


    # Get the form data from the request
    gejala1 = request.form['gejala1']
    gejala2 = request.form['gejala2']
    gejala3 = request.form['gejala3']


    features = [[gejala1, gejala2, gejala3]]


    prediction = model.predict(features)


    # Kondisi untuk memberikan rekomendasi nama dokter berdasarkan prediksi
    if prediction == "urologi":
        spesialis = "Urologi"
    elif prediction == "kulit dan kelamin":
        spesialis = "Kulit dan kelamin"
    elif prediction == "jantung dan pembuluh darah":
        spesialis = "Jantung dan pembuluh darah"
    elif prediction == "saraf dan neurolog":
        spesialis = "Saraf dan neurolog"
    elif prediction == "penyakit dalam":
        spesialis = "Penyakit dalam"
    elif prediction == "gastroenterologi":
        spesialis = "Gastroenterologi"
    elif prediction == "paru":
        spesialis = "Paru"
    elif prediction == "endokrinologi":
        spesialis = "Endokrinologi"
    else:
        spesialis = ""


    # Membuat objek cursor
    cursor = conn.cursor()


    # Mengambil data dokter berdasarkan spesialis
    query = "SELECT nama_dokter, gender_dokter FROM dokter WHERE spesialis=%s"
    cursor.execute(query, (spesialis,))
    result = cursor.fetchall()


    # Membuat objek Dokter dari hasil query
    rekomendasi_dokter = []
    for row in result:
        nama_dokter = row[0]
        gender_dokter = row[1]
        ## harga = row[2]
        dokter = Dokter(nama_dokter, gender_dokter, spesialis)
        rekomendasi_dokter.append(dokter)


    # Mengambil id_user dari tabel users berdasarkan uname_user
    query_user = "SELECT id_user FROM users WHERE uname_user = %s"
    cursor.execute(query_user, (session['uname_user'],))
    user_result = cursor.fetchone()
    id_user = user_result[0]


    # Query untuk menyimpan histori ke dalam tabel "rekam_histori"
    query_histori = "INSERT INTO rekam_histori (id_user, uname_user, gejala1, gejala2, gejala3, spesialis, waktu) VALUES (%s, %s, %s, %s, %s, %s, NOW())"
    values_histori = (id_user, session['uname_user'], gejala1, gejala2, gejala3, spesialis)
    cursor.execute(query_histori, values_histori)


    # Melakukan commit perubahan ke database
    conn.commit()


    # Menutup kursor
    cursor.close()


    # Render template HTML dan kirimkan hasil prediksi dan rekomendasi dokter ke dalam template
    return render_template('rekomendasi.html', prediction=prediction, spesialis=spesialis, rekomendasi_dokter=rekomendasi_dokter)


def test_input(data):
    data = data.strip()
    data = data.replace('\\', '\\\\')
    data = data.replace('"', '\\"')
    data = data.replace("'", "\\'")
    data = data.replace('<', '&lt;')
    data = data.replace('>', '&gt;')
    return data


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nama_user = test_input(request.form['nama_user'])
        uname_user = test_input(request.form['uname_user'])
        email = test_input(request.form['email'])
        password_user = test_input(request.form['password_user'])


        cursor = conn.cursor()


        # Lakukan operasi penyimpanan data ke database di sini
        query = "INSERT INTO users (nama_user, uname_user, email, password_user) VALUES (%s, %s, %s, %s)"
        values = (nama_user, uname_user, email, password_user)
        cursor.execute(query, values)


        # Melakukan commit perubahan ke database
        conn.commit()


        # Menutup kursor
        cursor.close()


        return redirect('/login')  # Ganti '/login' dengan halaman tujuan setelah registrasi


    return render_template('signup.html')  # Ganti 'signup.html' dengan nama template yang sesuai




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname_user = request.form['uname_user']
        password_user = request.form['password_user']


        # Membuat objek cursor
        cursor = conn.cursor()


        # Mengecek keberadaan pengguna di database
        query = "SELECT COUNT(*) FROM users WHERE uname_user=%s AND password_user=%s"
        cursor.execute(query, (uname_user, password_user))
        result = cursor.fetchone()


        # Menutup kursor
        cursor.close()


        if result[0] > 0:
            session['uname_user'] = uname_user  # Menyimpan sesi login
            return redirect(url_for('home'))
        else:
            return 'Invalid username or password'


    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('uname_user', None)  # Menghapus sesi login
    return redirect(url_for('home'))


@app.route('/rekam_histori')
def rekam_histori():
    if 'uname_user' in session:
        # Membuat objek cursor
        cursor = conn.cursor()


        # Mengambil rekam histori berdasarkan uname_user
        query = "SELECT rh.waktu, g1.gejala AS gejala1, g2.gejala AS gejala2, g3.gejala AS gejala3, rh.spesialis FROM rekam_histori AS rh LEFT JOIN gejala AS g1 ON rh.gejala1 = g1.id LEFT JOIN gejala AS g2 ON rh.gejala2 = g2.id LEFT JOIN gejala AS g3 ON rh.gejala3 = g3.id WHERE uname_user = %s ORDER BY waktu DESC"
        cursor.execute(query, (session['uname_user'],))
        result = cursor.fetchall()


        # Menutup kursor
        cursor.close()


        # Mengirim hasil rekam histori ke dalam template
        return render_template("rekam_histori.html", rekam_histori=result)
    else:
        return redirect(url_for('login'))


@app.route('/chat/<dokter_id>', methods=['GET'])
def chat(dokter_id):
    # Check session for authentication
    if 'uname_user' not in session:
        return redirect(url_for('login'))


    # Membuat objek cursor
    cursor = conn.cursor()


    # Mengambil id_user dari tabel users berdasarkan uname_user
    query_user = "SELECT id_user FROM users WHERE uname_user = %s"
    cursor.execute(query_user, (session['uname_user'],))
    user_result = cursor.fetchone()
    id_user = user_result[0]


    # Query untuk menyimpan chat ke dalam tabel "messages"
    query_chat = "INSERT INTO messages (id_user, id_dokter, message, waktu) VALUES (%s, %s, %s, NOW())"
    values_chat = (id_user, dokter_id, messages)
    cursor.execute(query_chat, values_chat)


    # Melakukan commit perubahan ke database
    conn.commit()


    # Menutup kursor
    cursor.close()


    return redirect(url_for('chat', dokter_id=dokter_id))


if __name__ == '__main__':
    app.run(debug=True)
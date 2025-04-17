from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import os
import re
import time,mimetypes,hashlib
import base64
from werkzeug.utils import secure_filename
import base64
import tempfile
from moviepy.editor import AudioFileClip, concatenate_audioclips
from PIL import Image
import tempfile
import hashlib
from moviepy.editor import ImageClip, concatenate_videoclips
import io
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.editor import *
import psycopg2
from psycopg2 import OperationalError

app = Flask(__name__)

app.secret_key = 'dev'
app.config['DATABASE'] = 'postgresql'
app.config['DB_HOST'] = 'slimed-sheep-8953.8nk.gcp-asia-southeast1.cockroachlabs.cloud'
app.config['DB_PORT'] = '26257'
app.config['DB_USER'] = 'dev'
app.config['DB_PASSWORD'] = 'PLNp6FxiYPewx696lpWsEw'
app.config['DB_NAME'] = 'project'

def connect_to_database():
    try:
        conn = psycopg2.connect(
            dbname=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            host=app.config['DB_HOST'],
            port=app.config['DB_PORT'],
            sslmode='verify-full'
        )
        return conn
        
    except OperationalError as e:
        print(f"Error: {e}")
        return None

mysql = MySQL(app)

hello_name = 'hi'
hello_id = 1
selected_images_all = []
audio_all = []
transitions_all = []
duration_all = []

def hash_password(password):
    # Encode the password to bytes before hashing
    password_bytes = password.encode('utf-8')
    
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()
    
    # Update the hash object with the password bytes
    sha256_hash.update(password_bytes)
    
    # Get the hexadecimal representation of the hash digest
    hashed_password = sha256_hash.hexdigest()
    
    return hashed_password

def verify_password(password, hashed_password):
    # Hash the input password using the same method
    input_hashed_password = hash_password(password)
    
    # Compare the two hashed passwords
    if input_hashed_password == hashed_password:
        return True
    else:
        return False

def convertToBinaryData(filename):
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def get_last_part_after_slash(filepath):
    return filepath.split('/')[-1]
            
import base64

def get_images(user_id):
    conn = None
    try:
        conn = connect_to_database()
        with conn.cursor() as cursor:
            cursor.execute('SELECT name, data FROM images WHERE user_id = %s', (user_id,))
            images = cursor.fetchall()
            return images
    except Exception as e:
        print(f"Error fetching images: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_images2(user_id):
    try:
        conn = connect_to_database()
        if conn is not None:
            cur = conn.cursor()
            # Construct the SQL query with placeholders for selected_images_all
            query = """
                SELECT name, data
                FROM images
                WHERE user_id = %s AND name IN %s
            """
            print(selected_images_all)
            # Pass user_id and selected_images_all as parameters
            cur.execute(query, (user_id, tuple(selected_images_all)))
            images = cur.fetchall()
            cur.close()
            conn.close()
            return images
        else:
            print("Failed to connect to the database.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def encode_images_to_base64(images):
    encoded_images = []
    for name, data in images:
        # Convert binary data to base64
        encoded_data = base64.b64encode(data).decode('utf-8')
        # Append the name and encoded data as a dictionary to the encoded_images list
        encoded_images.append({'name': name, 'data': encoded_data})
    return encoded_images

@app.route('/get_images2')
def get_user_images2():
    user_id = session.get('userid')
    if user_id:
        images = get_images2(user_id)
        if images:
            encoded_images = encode_images_to_base64(images)
        return jsonify({'images': encoded_images})
    else:
        return jsonify({'images': []})

@app.route('/get_images')
def your_function():
    user_id = session.get('userid')
    print(user_id)
    if user_id:
        images = get_images(user_id)
        if images:
            encoded_images = encode_images_to_base64(images)
            return jsonify({'images': encoded_images})
        else:
            return jsonify({'message': 'No images found for the user.'})
    else:
        return jsonify({'message': 'User ID not found in session.'})

@app.route('/')
@app.route('/landing_page', methods=['GET', 'POST'])
def landing_page():
    return render_template('landing_page.html')


@app.route('/video_edit', methods=['GET', 'POST'])
def video_edit():
    print("QWERTY")
    time.sleep(20)
    return render_template('video_edit.html',user_home_name = session['name'])


@app.route('/get_audio')
def get_audio():
    try:
        conn = connect_to_database()
        if conn is not None:
            cur = conn.cursor()
            # Execute the SQL query to select audio names
            cur.execute('SELECT audio_name FROM audio')
            audio_files = cur.fetchall()
            cur.close()
            conn.close()
            
            # Extract audio names from the list of tuples
            audio_names = [audio[0] for audio in audio_files]
            
            print(audio_names)
            
            return jsonify({'audio_names': audio_names})
        else:
            print("Failed to connect to the database.")
            return jsonify({'error': 'Failed to connect to the database.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching audio names.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    global hello_name
    global hello_id
    message = ''
    alert_message = ''  # Initialize alert message
    
    if session.get('remember_me'):
        if session['email'] == 'admin@gmail.com':
            return render_template('admin.html')
        else:
            return redirect(url_for('user_home'))
    
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        remember_me = True if 'remember_me' in request.form else False  # Check if Remember Me is checked
        
        conn = connect_to_database()
        try:
            if conn is not None:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s', (email,))
                user = cur.fetchone()
                if user:
                    if verify_password(password, user[3]):  # Assuming password is stored in the 4th column (index 3)
                        session['loggedin'] = True
                        session['userid'] = user[0]  # Assuming user_id is stored in the 1st column (index 0)
                        session['name'] = user[1]  # Assuming username is stored in the 2nd column (index 1)
                        session['email'] = user[2]  # Assuming email is stored in the 3rd column (index 2)
                        session['remember_me'] = remember_me  # Store Remember Me status in session
                        hello_name = user[1]  # Assuming username is stored in the 2nd column (index 1)
                        hello_id = user[0]  # Assuming user_id is stored in the 1st column (index 0)
                        message = 'Logged in successfully!'
                        if email == 'admin@gmail.com' and password == 'admin':
                            # Redirect to admin page if the credentials match admin credentials
                            return render_template('admin.html', user_home_name=user[1])  # Assuming username is stored in the 2nd column (index 1)
                        else:
                            return render_template('user_home.html', user_home_name=user[1])  # Assuming username is stored in the 2nd column (index 1)
                    else:
                        alert_message = 'Incorrect password!'  # Set alert message for incorrect password
                else:
                    alert_message = 'User not found!'  # Set alert message for user not found
        except Exception as e:
            message = f'Error: {e}'
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    
    return render_template('mylogin.html', message=message, alert_message=alert_message)    

@app.route('/upload_images', methods=['GET', 'POST'])
def upload_images():
    global hello_id
    if request.method == 'POST':
        time.sleep(4) 
        files = request.files.getlist('input_file')
        
        # Establish database connection
        conn = connect_to_database()
        cursor = conn.cursor()

        for file in files:
            if file.filename == '':
                continue
            filename = secure_filename(file.filename)
            data = file.read()
            email = session['email']
            file_size = len(data)/1024
            mime_type = mimetypes.guess_type(filename)[0]
            cursor.execute('INSERT INTO images (user_id, name, size, email,mimetype, data) VALUES (%s, %s,%s, %s, %s, %s)',
                           (hello_id, filename, file_size, email,mime_type, data))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return redirect(url_for('user_home'))
    else:
        return render_template('upload_images.html', user_home_name=hello_name)

@app.route('/user_home', methods=['GET', 'POST'])
def user_home():
    if 'loggedin' in session and session['loggedin']:
        if 'userid' in session:
            user_id = session['userid']
            user_images = get_images(user_id)
            return render_template('user_home.html', user_home_name=session['name'], user_images=user_images)
        else:
            return "User ID not found in session"
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    session.pop('remember_me', None)
    session.clear()
    return redirect(url_for('landing_page'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        hashed_password = hash_password(password)
        
        conn = connect_to_database()
        try:
            if conn is not None:
                cur = conn.cursor()
                cur.execute('SELECT * FROM users WHERE email = %s', (email,))
                account = cur.fetchone()
                if account:
                    message = 'Account already exists!'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                    message = 'Invalid email address!'
                elif not userName or not password or not email:
                    message = 'Please fill out the form!'
                else:
                    cur.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (userName, email, hashed_password,))
                    conn.commit()
                    message = 'You have successfully registered!'
        except Exception as e:
            message = f'Error: {e}'
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
                
        return render_template('mylogin.html', message=message)
    else:
        message = 'Please fill out the form!'
        return render_template('mysignup.html', message=message)

@app.route('/video_slideshow', methods=['GET', 'POST'])
def video_slideshow():
    time.sleep(60)
    return render_template('video_slideshow.html',user_home_name = session['name'])

def get_audio_files():
    # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    conn = connect_to_database()
    cur = conn.cursor()
    cur.execute('SELECT * FROM audio')
    audio_files = cur.fetchall()
    # cursor.execute('SELECT * FROM audio')
    # audio_files = cursor.fetchall()
    # cursor.close()
    return audio_files

@app.route('/get_selected_images', methods=['POST'])
def get_selected_images():
    print("PYUIO")
    selected_images = request.json.get('selectedImages')
    user_id = hello_id  # Assuming you store user_id in session

    cursor = mysql.connection.cursor()
    selected_images_data = []
    for image_name in selected_images:
        cursor.execute("SELECT name, data FROM images WHERE name = %s AND user_id = %s", (image_name, user_id,))
        result = cursor.fetchone()
        if result:
            image_name, image_data = result
            selected_images_data.append({'name': image_name, 'data': image_data})
    cursor.close()

    return jsonify({'images': selected_images_data})


@app.route('/create_video', methods=['POST','GET'])
def create_video():
    global selected_images_all
    previous_response = selected_images_all
    selected_images = request.json.get('selectedImages')
    selected_images_all = selected_images
    
    print(selected_images_all)
    
    if selected_images_all == []:
        selected_images_all = previous_response
    
    common_image_size = (1920, 1080)  # Adjust dimensions as needed
    resized_images = []

    # Fetch user_id from session
    user_id = hello_id  # Assuming you store user_id in session

    # Fetch images from the database based on image name and user_id
    print("HIIIII")
    conn = connect_to_database()
    if conn is not None:
        try:
            cursor = conn.cursor()
            for image_name in selected_images:
                cursor.execute("SELECT data FROM images WHERE name = %s AND user_id = %s", (image_name, user_id,))
                result = cursor.fetchone()
                if result:
                    image_data = result[0]
                    # Process the image data as needed (resize, save to temporary file, etc.)
                    image = Image.open(io.BytesIO(image_data))
                    resized_image = image.resize(common_image_size)
                    resized_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
                    resized_image.save(resized_image_path)
                    resized_images.append(resized_image_path)
            cursor.close()
        except psycopg2.Error as e:
            print(f"Error: {e}")
            return jsonify({'error': 'Error retrieving images from the database'})
        finally:
            conn.close()
            
            
    print("BYEEEEE")

    if not resized_images:
        # If no images were found, return an error response
        return jsonify({'error': 'No images found for the provided image names and user_id'})

    selected_audio_id = 1  # Example selected audio ID (replace with actual user input)
    selected_audio_path = ''
            
    print("POOOOO")

    # audio_clip = AudioFileClip(selected_audio_path)
    image_duration = 3  # Example duration of each image in seconds
    # num_repeats = int(len(resized_images) * image_duration / audio_clip.duration) + 1
    # audio_clips = [audio_clip] * num_repeats
    # concatenated_audio_clip = concatenate_audioclips(audio_clips)
    clips_with_effects = []
    for image_path in resized_images:
        clip = ImageClip(image_path).set_duration(image_duration)
        clips_with_effects.append(clip)
    final_clip = concatenate_videoclips(clips_with_effects)
    # final_clip = final_clip.set_audio(concatenated_audio_clip)
    output_filename = f'output1.mp4'
    output_path = os.path.join('static', output_filename)
    final_clip.write_videofile(output_path, fps=10)

    return redirect(url_for('video_edit'))

@app.route('/create_video_high', methods=['POST'])
def create_video_high():
    global selected_images_all,transitions_all,audio_all,duration_all
    data = request.get_json()
    # selected_images = data['selectedImages']
    
    
    
    image_durations = [int(duration) for duration in data.get('imageDurations', [])]  # Convert durations to integers
    print(image_durations)
    previous_durations = duration_all
    duration_all = [image_durations]
    
    
    
    # audio_files = get_audio_files()
    previous_transition = transitions_all
    transitions = data['imageTransitions']
    transitions_all = transitions
    print(transitions)
    audio_names = data.get('selectedAudios', [])  # Get selected audio names
    print(audio_names)
    audio_durations = [float(duration) for duration in data.get('audioDurations', [])]  # Convert durations to floats
    print(selected_images_all)
        

    common_image_size = (1920, 1080) 
    resized_images = []

    conn = connect_to_database()
    cursor = conn.cursor()
    for i, image_name in enumerate(selected_images_all):
        cursor.execute("SELECT data FROM images WHERE name = %s AND user_id = %s", (image_name, hello_id,))
        result = cursor.fetchone()
        if result:
            image_data = result[0]
            image = Image.open(io.BytesIO(image_data))
            resized_image = image.resize(common_image_size)
            resized_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            resized_image.save(resized_image_path)
            resized_images.append((resized_image_path, image_durations[i]))
    cursor.close()

    if not resized_images:
        return jsonify({'error': 'No images found for the provided image names and user_id'})

    selected_audio_paths = []  # List to hold paths of selected audio files

    # Retrieve audio data and save them as temporary files
    for audio_name, duration in zip(audio_names, audio_durations):
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT audio_data FROM audio WHERE audio_name = %s", (audio_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            audio_data = result[0]
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                temp_audio_file.write(audio_data)
                selected_audio_paths.append(temp_audio_file.name)

    # Load audio files
    audio_clips = []
    for audio_path, duration in zip(selected_audio_paths, audio_durations):
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration < duration:
            # If the audio clip duration is less than the input duration, repeat the audio clip
            num_repeats = int(duration / audio_clip.duration) + 1
            repeated_audio_clip = concatenate_audioclips([audio_clip] * num_repeats)
            audio_clips.append(repeated_audio_clip.set_duration(duration))
        else:
            audio_clips.append(audio_clip.set_duration(duration))
    
    concatenated_audio_clip = concatenate_audioclips(audio_clips)

    clips_with_effects = []
    
    for (image_path, duration), transition in zip(resized_images, transitions):
        clip = ImageClip(image_path).set_duration(duration)
        if transition == "fade-in":
            clip = fadein(clip, duration=duration)  # Apply fade-in effect
        elif transition == "fade-out":
            clip = fadeout(clip, duration=duration)  # Apply fade-out effect
        elif transition == "fade-in-out":
            clip = fadein(clip, duration=duration/2).fadeout(duration=duration/2)  # Apply fade-in/fade-out effect
        clips_with_effects.append(clip)
        
    final_clip = concatenate_videoclips(clips_with_effects)

    # Set audio for the image sequence
    final_clip = final_clip.set_audio(concatenated_audio_clip)

    output_filename = f'output1.mp4'
    output_path = os.path.join('static', output_filename)
    final_clip.write_videofile(output_path, fps=10)

    video_url = 'url_to_new_video.mp4'

    return jsonify({'video_url': video_url})

@app.route('/create_video_medium', methods=['POST'])
def create_video_medium():
    global selected_images_all
    data = request.get_json()
    # selected_images = data['selectedImages']
    image_durations = [int(duration) for duration in data.get('imageDurations', [])]  # Convert durations to integers
    # audio_files = get_audio_files()
    previous_response = selected_images_all
    transitions = data['imageTransitions']
    audio_names = data.get('selectedAudios', [])  # Get selected audio names
    audio_durations = [float(duration) for duration in data.get('audioDurations', [])]  # Convert durations to floats

    common_image_size = (720, 480)
    resized_images = []

    conn = connect_to_database()
    cursor = conn.cursor()
    for i, image_name in enumerate(selected_images_all):
        cursor.execute("SELECT data FROM images WHERE name = %s AND user_id = %s", (image_name, hello_id,))
        result = cursor.fetchone()
        if result:
            image_data = result[0]
            image = Image.open(io.BytesIO(image_data))
            resized_image = image.resize(common_image_size)
            resized_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            resized_image.save(resized_image_path)
            resized_images.append((resized_image_path, image_durations[i]))
    cursor.close()

    if not resized_images:
        return jsonify({'error': 'No images found for the provided image names and user_id'})

    selected_audio_paths = []  # List to hold paths of selected audio files

    # Retrieve audio data and save them as temporary files
    for audio_name, duration in zip(audio_names, audio_durations):
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT audio_data FROM audio WHERE audio_name = %s", (audio_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            audio_data = result[0]
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                temp_audio_file.write(audio_data)
                selected_audio_paths.append(temp_audio_file.name)

    # Load audio files
    audio_clips = []
    for audio_path, duration in zip(selected_audio_paths, audio_durations):
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration < duration:
            # If the audio clip duration is less than the input duration, repeat the audio clip
            num_repeats = int(duration / audio_clip.duration) + 1
            repeated_audio_clip = concatenate_audioclips([audio_clip] * num_repeats)
            audio_clips.append(repeated_audio_clip.set_duration(duration))
        else:
            audio_clips.append(audio_clip.set_duration(duration))
    
    concatenated_audio_clip = concatenate_audioclips(audio_clips)

    clips_with_effects = []
    
    for (image_path, duration), transition in zip(resized_images, transitions):
        clip = ImageClip(image_path).set_duration(duration)
        if transition == "fade-in":
            clip = fadein(clip, duration=duration)  # Apply fade-in effect
        elif transition == "fade-out":
            clip = fadeout(clip, duration=duration)  # Apply fade-out effect
        elif transition == "fade-in-out":
            clip = fadein(clip, duration=duration/2).fadeout(duration=duration/2)  # Apply fade-in/fade-out effect
        clips_with_effects.append(clip)
        
    final_clip = concatenate_videoclips(clips_with_effects)

    # Set audio for the image sequence
    final_clip = final_clip.set_audio(concatenated_audio_clip)

    output_filename = f'output2.mp4'
    output_path = os.path.join('static', output_filename)
    final_clip.write_videofile(output_path, fps=10)

    video_url = 'url_to_new_video.mp4'

    return jsonify({'video_url': video_url})

@app.route('/create_video_low', methods=['POST'])
def create_video_low ():
    print("1")
    global selected_images_all
    data = request.get_json()
    selected_images = data['selectedImages']
    image_durations = [int(duration) for duration in data.get('imageDurations', [])]  # Convert durations to integers
    audio_files = get_audio_files()
    previous_response = selected_images_all
    transitions = data['imageTransitions']
    audio_names = data.get('selectedAudios', [])  # Get selected audio names
    audio_durations = [float(duration) for duration in data.get('audioDurations', [])]  # Convert durations to floats
    
    if selected_images_all == []:
        selected_images_all = previous_response

    common_image_size = (240, 144) 
    resized_images = []

    conn = connect_to_database()
    cursor = conn.cursor()
    for i, image_name in enumerate(selected_images_all):
        cursor.execute("SELECT data FROM images WHERE name = %s AND user_id = %s", (image_name, hello_id,))
        result = cursor.fetchone()
        if result:
            image_data = result[0]
            image = Image.open(io.BytesIO(image_data))
            resized_image = image.resize(common_image_size)
            resized_image_path = tempfile.NamedTemporaryFile(delete=False, suffix='.png').name
            resized_image.save(resized_image_path)
            resized_images.append((resized_image_path, image_durations[i]))
    cursor.close()

    if not resized_images:
        return jsonify({'error': 'No images found for the provided image names and user_id'})

    selected_audio_paths = []  # List to hold paths of selected audio files

    # Retrieve audio data and save them as temporary files
    for audio_name, duration in zip(audio_names, audio_durations):
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT audio_data FROM audio WHERE audio_name = %s", (audio_name,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            audio_data = result[0]
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                temp_audio_file.write(audio_data)
                selected_audio_paths.append(temp_audio_file.name)

    # Load audio files
    audio_clips = []
    for audio_path, duration in zip(selected_audio_paths, audio_durations):
        audio_clip = AudioFileClip(audio_path)
        if audio_clip.duration < duration:
            # If the audio clip duration is less than the input duration, repeat the audio clip
            num_repeats = int(duration / audio_clip.duration) + 1
            repeated_audio_clip = concatenate_audioclips([audio_clip] * num_repeats)
            audio_clips.append(repeated_audio_clip.set_duration(duration))
        else:
            audio_clips.append(audio_clip.set_duration(duration))
    
    concatenated_audio_clip = concatenate_audioclips(audio_clips)

    clips_with_effects = []
    
    for (image_path, duration), transition in zip(resized_images, transitions):
        clip = ImageClip(image_path).set_duration(duration)
        if transition == "fade-in":
            clip = fadein(clip, duration=duration)  # Apply fade-in effect
        elif transition == "fade-out":
            clip = fadeout(clip, duration=duration)  # Apply fade-out effect
        elif transition == "fade-in-out":
            clip = fadein(clip, duration=duration/2).fadeout(duration=duration/2)  # Apply fade-in/fade-out effect
        clips_with_effects.append(clip)
        
    final_clip = concatenate_videoclips(clips_with_effects)

    # Set audio for the image sequence
    final_clip = final_clip.set_audio(concatenated_audio_clip)

    output_filename = f'output3.mp4'
    output_path = os.path.join('static', output_filename)
    final_clip.write_videofile(output_path, fps=10)

    video_url = 'url_to_new_video.mp4'

    return jsonify({'video_url': video_url})

@app.route('/users')
def get_users():
    try:
        conn = connect_to_database()
        if conn is not None:
            cur = conn.cursor()
            # Query to select all users with their photo count
            cur.execute("""
            SELECT u.user_id, u.username, u.email, 
                   (SELECT COUNT(*) FROM images i WHERE i.user_id = u.user_id) AS photo_count
            FROM users u
            """)
            users = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify(users)
        else:
            print("Failed to connect to the database.")
            return jsonify({'error': 'Failed to connect to the database.'})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while fetching users.'})

@app.route('/delete_user/<email>', methods=['POST'])
def delete_user(email):
    try:
        conn = connect_to_database()
        if conn is not None:
            print(email)
            print(type(email))

            
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            user_id = cur.fetchone()  # Corrected method name
            conn.commit()
            cur.close()

            print(user_id)
            print("DELETED")
            
            return jsonify({'message': 'User deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to connect to the database'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
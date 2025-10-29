import os
import cv2
import numpy as np
import threading
import time
import datetime
import platform
from flask import Flask, render_template, Response, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Context processor to add current datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Configuration
UPLOAD_FOLDER = 'static/captures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables
camera = None
output_frame = None
lock = threading.Lock()
motion_detected = False
last_motion_time = None
motion_threshold = 5000  # Adjust based on sensitivity needs
frame_count = 0

# Settings (would be stored in a database in production)
settings = {
    'email': {
        'enabled': False,
        'smtp_server': '',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'recipient': ''
    },
    'twilio': {
        'enabled': False,
        'account_sid': '',
        'auth_token': '',
        'from_number': '',
        'to_number': ''
    }
}

# Store motion events
motion_events = []


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def detect_motion(frame1, frame2):
    # Convert frames to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # Compute the absolute difference between frames
    frame_diff = cv2.absdiff(gray1, gray2)
    
    # Apply threshold to highlight differences
    thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)[1]
    
    # Dilate the thresholded image to fill in holes
    thresh = cv2.dilate(thresh, None, iterations=2)
    
    # Find contours on thresholded image
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Calculate total area of all contours
    total_area = sum([cv2.contourArea(c) for c in contours])
    
    return total_area > motion_threshold, thresh, contours


def send_email_alert(image_path):
    if not settings['email']['enabled']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = settings['email']['username']
        msg['To'] = settings['email']['recipient']
        msg['Subject'] = 'Motion Detected - Security Camera Alert'
        
        body = f"Motion was detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach image
        with open(image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)
        
        # Connect to server and send email
        server = smtplib.SMTP(settings['email']['smtp_server'], settings['email']['smtp_port'])
        server.starttls()
        server.login(settings['email']['username'], settings['email']['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_sms_alert(image_url):
    if not settings['twilio']['enabled']:
        return False
    
    try:
        client = Client(settings['twilio']['account_sid'], settings['twilio']['auth_token'])
        message = client.messages.create(
            body=f"Motion detected at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. View image: {image_url}",
            from_=settings['twilio']['from_number'],
            to=settings['twilio']['to_number']
        )
        return True
    except Exception as e:
        print(f"SMS error: {e}")
        return False


def generate_frames():
    global camera, output_frame, lock, motion_detected, last_motion_time, frame_count, motion_events
    
    # Initialize camera
    if camera is None:
        try:
            camera = cv2.VideoCapture(0)  # Use 0 for webcam
            if not camera.isOpened():
                print("Error: Could not open camera.")
                # Create a blank frame with error message for display
                blank_frame = np.zeros((480, 640, 3), np.uint8)
                cv2.putText(blank_frame, "Camera not available", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                with lock:
                    output_frame = blank_frame.copy()
                return
        except Exception as e:
            print(f"Camera error: {e}")
            # Create a blank frame with error message for display
            blank_frame = np.zeros((480, 640, 3), np.uint8)
            cv2.putText(blank_frame, "Camera not available", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            with lock:
                output_frame = blank_frame.copy()
            return
    
    # Initialize previous frame
    _, prev_frame = camera.read()
    
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        # Process every other frame to reduce CPU usage
        if frame_count % 2 == 0:
            # Detect motion
            motion, thresh, contours = detect_motion(prev_frame, frame)
            
            # Update previous frame
            prev_frame = frame.copy()
            
            # Draw contours on frame
            frame_with_contours = frame.copy()
            cv2.drawContours(frame_with_contours, contours, -1, (0, 255, 0), 2)
            
            # Add timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame_with_contours, timestamp, (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Handle motion detection
            current_time = time.time()
            if motion:
                # Only trigger a new alert if it's been more than 5 seconds since the last one
                if last_motion_time is None or (current_time - last_motion_time) > 5:
                    motion_detected = True
                    last_motion_time = current_time
                    
                    # Save the frame
                    filename = f"motion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    cv2.imwrite(filepath, frame)
                    
                    # Add to motion events
                    motion_events.insert(0, {
                        'timestamp': timestamp,
                        'image': filename,
                        'path': filepath
                    })
                    
                    # Keep only the last 20 events
                    if len(motion_events) > 20:
                        motion_events = motion_events[:20]
                    
                    # Send alerts
                    threading.Thread(target=send_email_alert, args=(filepath,)).start()
                    # In a real app, you'd have a proper URL
                    threading.Thread(target=send_sms_alert, args=(f"http://yourdomain.com/static/captures/{filename}",)).start()
            
            # Update the output frame with contours
            with lock:
                output_frame = frame_with_contours.copy()
        
        frame_count += 1
        
        # Artificial delay to reduce CPU usage
        time.sleep(0.01)


def generate_video_feed():
    global output_frame, lock
    
    while True:
        with lock:
            if output_frame is None:
                continue
            
            # Encode the frame as JPEG
            (flag, encoded_image) = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue
        
        # Yield the output frame in byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encoded_image) + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html', settings=settings, motion_events=motion_events)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', motion_events=motion_events)


@app.route('/settings')
def settings_page():
    import flask
    import cv2
    import platform
    return render_template('settings.html', settings=settings, flask=flask, cv2=cv2, platform=platform)


@app.route('/video_feed')
def video_feed():
    return Response(generate_video_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/motion_events')
def get_motion_events():
    try:
        # Add a small delay to prevent overwhelming the server with requests
        time.sleep(0.1)
        return jsonify(motion_events)
    except Exception as e:
        app.logger.error(f"Error in get_motion_events: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    global settings
    
    # Update email settings
    settings['email']['enabled'] = 'email_enabled' in request.form
    settings['email']['smtp_server'] = request.form.get('smtp_server', '')
    settings['email']['smtp_port'] = int(request.form.get('smtp_port', 587))
    settings['email']['username'] = request.form.get('email_username', '')
    if request.form.get('email_password'):
        settings['email']['password'] = request.form.get('email_password')
    settings['email']['recipient'] = request.form.get('email_recipient', '')
    
    # Update Twilio settings
    settings['twilio']['enabled'] = 'twilio_enabled' in request.form
    settings['twilio']['account_sid'] = request.form.get('twilio_account_sid', '')
    if request.form.get('twilio_auth_token'):
        settings['twilio']['auth_token'] = request.form.get('twilio_auth_token')
    settings['twilio']['from_number'] = request.form.get('twilio_from_number', '')
    settings['twilio']['to_number'] = request.form.get('twilio_to_number', '')
    
    flash('Settings updated successfully!', 'success')
    return redirect(url_for('settings_page'))


if __name__ == '__main__':
    # Start a thread that will perform motion detection
    t = threading.Thread(target=generate_frames)
    t.daemon = True
    t.start()
    
    app.run(debug=True, threaded=True)
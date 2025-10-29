# Security Camera

A modern, responsive webcam-based motion detection security system built with Flask, OpenCV, and Bootstrap.

![Security Camera](https://via.placeholder.com/1200x600/0d6efd/ffffff?text=Security+Camera)

## Features

- **Real-time Motion Detection**: Uses OpenCV to detect motion in webcam feed
- **Email Alerts**: Sends email notifications with snapshots when motion is detected
- **SMS Notifications**: Integrates with Twilio to send SMS alerts
- **Responsive Dashboard**: View and manage motion events with timestamps and thumbnails
- **Configurable Settings**: Customize email, SMS, camera, and motion detection settings
- **Modern UI**: Built with Bootstrap 5 for a clean, intuitive interface

## Requirements

- Python 3.7+
- Webcam or IP camera
- SMTP email account (for email notifications)
- Twilio account (for SMS notifications, optional)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/security-camera.git
   cd security-camera
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Configuration

### Email Notifications

1. Navigate to the Settings page
2. Enable Email Notifications
3. Enter your SMTP server details:
   - SMTP Server (e.g., smtp.gmail.com)
   - SMTP Port (e.g., 587 for TLS)
   - Email Username
   - Email Password
   - Recipient Email

### SMS Notifications

1. Create a [Twilio account](https://www.twilio.com/)
2. Get your Account SID, Auth Token, and a Twilio phone number
3. Navigate to the Settings page
4. Enable SMS Notifications
5. Enter your Twilio credentials:
   - Account SID
   - Auth Token
   - Twilio Phone Number
   - Your Phone Number

## Project Structure

```
security-camera/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── static/                # Static files
│   ├── css/               # CSS stylesheets
│   │   └── style.css      # Main stylesheet
│   ├── js/                # JavaScript files
│   │   └── main.js        # Main JavaScript file
│   └── captures/          # Captured motion images
└── templates/             # HTML templates
    ├── base.html          # Base template
    ├── index.html         # Home page with live feed
    ├── dashboard.html     # Motion events dashboard
    └── settings.html      # Configuration settings
```

## Usage

### Home Page

The home page displays the live camera feed and system status. Recent motion alerts are shown on the right side.

### Dashboard

The dashboard provides a comprehensive view of all motion events with timestamps and images. You can filter events by date and switch between grid, list, and timeline views.

### Settings

The settings page allows you to configure:

- Email notifications
- SMS notifications
- Camera settings
- Motion detection parameters

## Security Considerations

- This application is designed for local network use
- If exposing to the internet, implement proper authentication
- Store sensitive credentials securely (consider using environment variables)
- Regularly update dependencies to patch security vulnerabilities

## Troubleshooting

### Camera Issues

- Ensure your webcam is properly connected
- Check if other applications are using the camera
- Try changing the camera source in settings

### Email Notification Issues

- Verify SMTP server and port are correct
- For Gmail, you may need to enable "Less secure app access" or use an App Password
- Check your firewall settings

### SMS Notification Issues

- Verify your Twilio credentials are correct
- Ensure your Twilio account is active and funded
- Check that the phone number format includes country code



## Acknowledgments

- [Flask](https://flask.palletsprojects.com/)
- [OpenCV](https://opencv.org/)
- [Bootstrap](https://getbootstrap.com/)
- [Twilio](https://www.twilio.com/)

## 👨‍💻 Author
- **Syed Abdul Basith** 
  

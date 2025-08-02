# Eventure

Event Finder is a web application that allows users to discover, host, and book events with ease. Built using Python, Flask, and MongoDB, it features secure user authentication, event hosting with OTP verification, ticket booking with QR code generation, and email notifications.

## Features

- User registration and login with OTP verification  
- Host and manage events  
- Book tickets and receive QR codes via email  
- User profile management  
- Secure password reset  
- Event search and filtering  

## Tech Stack

- Python  
- Flask  
- MongoDB  
- Flask-Login  
- HTML/CSS/JS  

## Requirements

To run this project, make sure you have the following installed:

- Python 3.8 or higher  
- MongoDB (local or cloud instance)  
- pip (Python package installer)  
- A modern web browser (e.g., Chrome, Firefox)  
- An SMTP email account for OTP and ticket emails  
- Git (for cloning the repository)  

## Functions

- **User Registration with OTP**: Verifies user email before account creation using one-time password via SMTP.  
- **Login & Authentication**: Secure login using Flask-Login with session management.  
- **Event Hosting**: Authenticated users can create, edit, and delete events.  
- **Event Booking**: Users can book available events and receive ticket confirmation.  
- **QR Code Generation**: A unique QR code is generated for each booked ticket and emailed to the user.  
- **Email Notifications**: Sent for OTP, booking confirmations, and password reset requests.  
- **Search & Filter**: Events can be searched by keyword, category, or date.  
- **User Dashboard**: Users can manage their bookings, hosted events, and profile settings.  
- **Password Reset**: Secure password reset functionality using email verification.

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Aaron-hub-dev-maker/Event-Finder.git
   cd Event-Finder
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Start MongoDB** (make sure MongoDB is running on your system).

4. **Run the app:**
   ```sh
   python app.py
   ```

5. **Open your browser and go to:**  
   [http://localhost:5000](http://localhost:5000)


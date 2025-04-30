import sqlite3
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime, timedelta

# Database connection and query execution
def fetch_car_data(db_path, output_csv):
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Calculate the first and last day of the previous month
        today = datetime.today()
        first_day_of_current_month = datetime(today.year, today.month, 1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = datetime(last_day_of_previous_month.year, last_day_of_previous_month.month, 1)

        # SQL query to fetch dealership IDs with delivered contracts from the previous month
        contract_query = f"""
        SELECT DISTINCT dealership_id
        FROM contracts
        WHERE delivered_date BETWEEN '{first_day_of_previous_month.date()}' AND '{last_day_of_previous_month.date()}'
        """
        cursor.execute(contract_query)
        dealership_ids = [row[0] for row in cursor.fetchall()]

        if not dealership_ids:
            print("No contracts delivered in the previous month.")
            return

        # SQL query to fetch car data for the filtered dealership IDs with NULL or blank descriptions
        placeholders = ', '.join('?' for _ in dealership_ids)  # Create placeholders for the IN clause
        car_query = f"""
        SELECT car_id, make, dealership_id, description
        FROM cars
        WHERE dealership_id IN ({placeholders}) AND (description IS NULL OR description = '')
        """
        cursor.execute(car_query, dealership_ids)

        # Fetch all rows
        rows = cursor.fetchall()

        # Write data to CSV
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write header
            writer.writerow(['car_id', 'make', 'dealership_id', 'description'])
            # Write data rows
            writer.writerows(rows)

        print(f"Data exported to {output_csv} successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

# Email sending function
def send_email(smtp_server, port, sender_email, sender_password, recipient_email, subject, body, attachment_path):
    try:
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach email body
        msg.attach(MIMEText(body, 'plain'))

        # Attach the CSV file
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={os.path.basename(attachment_path)}'
            )
            msg.attach(part)

        # Connect to SMTP server and send email
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Main script
if __name__ == "__main__":
    # Database and CSV file paths
    database_path = "path_to_your_database.db"  # Replace with your database path
    csv_file_path = "car_data.csv"

    # Fetch data and export to CSV
    fetch_car_data(database_path, csv_file_path)

    # Email configuration
    smtp_server = "smtp.gmail.com"  # Replace with your SMTP server
    smtp_port = 587
    sender_email = "email@gmail.com"  # Replace with your email
    sender_password = "password"  # Replace with your email password
    recipient_email = "recipient_email@example.com"  # Replace with recipient email
    email_subject = "Car Data Export"
    email_body = "Please find attached car data."

    # Send email with CSV attachment
    send_email(smtp_server, smtp_port, sender_email, sender_password, recipient_email, email_subject, email_body, csv_file_path)
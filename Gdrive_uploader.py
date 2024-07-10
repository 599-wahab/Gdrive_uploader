import flet as ft
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
import os
import chardet  # Optional: for detecting encoding

# Authenticate and create GoogleDrive instance
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("credentials.json")  # Load existing credentials if available

    try:
        if gauth.credentials is None:
            # Authenticate if credentials are not available
            print("Authenticating for the first time...")
            gauth.LocalWebserverAuth()  # Use LocalWebserverAuth instead of CommandLineAuth
            gauth.SaveCredentialsFile("credentials.json")  # Save credentials for future use
        elif gauth.access_token_expired:
            # Refresh the token if it has expired
            print("Refreshing expired token...")
            gauth.Refresh()
            gauth.SaveCredentialsFile("credentials.json")
        else:
            # Initialize the saved credentials
            print("Using existing credentials...")
            gauth.Authorize()
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    
    return GoogleDrive(gauth)

# Convert CSV or XLSX to Excel and return the new file path
def convert_to_excel(file_path):
    try:
        file_name, file_ext = os.path.splitext(file_path)
        excel_file_path = f"{file_name}.xlsx"
        
        if file_ext.lower() == '.csv':
            # Detect encoding
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read())
            encoding = result['encoding']
            
            # Read CSV and save as Excel
            df = pd.read_csv(file_path, encoding=encoding)
            df.to_excel(excel_file_path, index=False)
        elif file_ext.lower() in ['.xls', '.xlsx']:
            # Read XLSX or XLS and save as Excel
            df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
            df.to_excel(excel_file_path, index=False)
        else:
            print(f"Unsupported file type: {file_ext}")
            return None
        
        return excel_file_path
    except Exception as e:
        print(f"Conversion error: {e}")
        return None

# Upload file to Google Drive
def upload_to_drive(drive, file_path):
    try:
        file_name = os.path.basename(file_path)
        gfile = drive.CreateFile({'title': file_name})
        gfile.SetContentFile(file_path)
        gfile.Upload()
        return f"File {file_name} uploaded to Google Drive."
    except Exception as e:
        print(f"Upload error: {e}")
        return f"Failed to upload file {file_name}."

# Flet app main function
def main(page: ft.Page):
    page.title = "Gdrive Uploader"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.auto_scroll = True

    drive = None  # GoogleDrive instance

    # File selection callback
    def on_file_selected(e):
        file_info = file_picker.result.files[0] if file_picker.result.files else None
        file_path = file_info.path if file_info else None
        print(f"File selected: {file_path}")
        if file_path:
            # Convert file to Excel format
            excel_file_path = convert_to_excel(file_path)
            if excel_file_path and drive:
                result.value = upload_to_drive(drive, excel_file_path)
            else:
                result.value = "Failed to convert file or authentication failed."
        else:
            result.value = "No file selected or authentication failed."
        page.update()

    # Authentication callback
    def on_auth_clicked(e):
        nonlocal drive
        drive = authenticate_drive()
        if drive:
            result.value = "Authenticated! Now you can upload files."
        else:
            result.value = "Failed to authenticate."
        page.update()

    # Flet components
    result = ft.Text(value="Please authenticate first.", size=16, weight="bold", text_align="center")
    auth_button = ft.ElevatedButton(text="Authenticate", on_click=on_auth_clicked)
    file_picker = ft.FilePicker(on_result=on_file_selected)
    upload_button = ft.ElevatedButton(text="Upload File", on_click=lambda _: file_picker.pick_files())  # Use pick_files
    
    # Add FilePicker to the page to initialize it
    page.overlay.append(file_picker)
    
    # Layout
    page.add(ft.Text(value="Gdrive Uploader", size=20, weight="bold", text_align="center"))
    page.add(auth_button)
    page.add(upload_button)
    page.add(result)

# Run Flet app
ft.app(target=main)

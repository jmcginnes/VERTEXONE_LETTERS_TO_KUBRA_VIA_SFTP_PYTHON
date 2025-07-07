# %%
#############################
# 
# Imports and Environment
#
#############################

import sys
import os
import paramiko
import datetime
from dotenv import load_dotenv

# Load environment variables
with open('.env', 'r') as envFile:
    load_dotenv(stream=envFile)

# Add shared libraries to path
sys.path.append(os.getenv('SHARED_LIBRARIES'))

# Custom libraries
from SharedLogger import createLogger
from O365Manager import sendEmail

# %%
#############################
# 
# Setup Program Info and Logging
#
#############################

programDirectory = os.getcwd()
programName = os.getenv('PROGRAM_NAME')
formattedDate = datetime.datetime.now().strftime("%Y-%m-%d")

log_folder = os.path.join(programDirectory, 'log')
os.makedirs(log_folder, exist_ok=True)

logger = createLogger(log_folder + '\\', programName + ' - ' + formattedDate + '.log')


# Load and clean distribution list
dl_raw = os.getenv('DL', '')
dl_list = [email.strip() for email in dl_raw.split(',') if email.strip()]
logger.info(f"DL from .env: {dl_list}")

# %%
#############################
# 
# Helper: Send Email to Distribution List
#
#############################

def sendToDistributionList(subject, body, dl_list, **kwargs):
    for recipient in dl_list:
        result = sendEmail(to=recipient, subject=subject, body=body, **kwargs)
        if result is True:
            logger.info(f"Email sent to {recipient}")
        else:
            logger.error(f"Failed to send email to {recipient}: {result}")

# %%
#############################
# 
# Function: Get Most Recent VP_ File from VertexOne SFTP
#
#############################

def fetch_latest_vp_file_from_sftp():
    try:
        host = os.getenv('SRC_SFTP_HOST')
        port = int(os.getenv('SRC_SFTP_PORT', 22))
        username = os.getenv('SRC_SFTP_USER')
        password = os.getenv('SRC_SFTP_PASSWORD')
        logger.info(f"Connecting to source SFTP: {host}:{port} as {username}")

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        file_list = sftp.listdir_attr('.')
        vp_files = [f for f in file_list if f.filename.startswith('VP_')]

        if not vp_files:
            raise FileNotFoundError("No files starting with 'VP_' found on VertexOne SFTP.")

        latest_file = max(vp_files, key=lambda f: f.st_mtime)
        local_dir = os.getenv('LOCAL_SAVE_PATH')
        os.makedirs(local_dir, exist_ok=True)

        base, ext = os.path.splitext(latest_file.filename)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        local_file_path = os.path.join(local_dir, f"{base}_{timestamp}{ext}")

        sftp.get(latest_file.filename, local_file_path)

        logger.info(f"Downloaded {latest_file.filename} to local path: {local_file_path}")

        sftp.close()
        transport.close()

        return local_file_path

    except Exception as e:
        logger.error(f"Failed to fetch VP_ file from VertexOne SFTP: {e}")
        raise

# %%
#############################
# 
# Function: Send File to Kubra SFTP
#
#############################

def send_file_to_kubra(file_path):
    try:
        host = os.getenv('DEST_SFTP_HOST')
        port = int(os.getenv('DEST_SFTP_PORT', 21))
        username = os.getenv('DEST_SFTP_USER')
        password = os.getenv('DEST_SFTP_PASSWORD')
        remote_dir = os.getenv('DEST_SFTP_PATH', '/')
        logger.info(f"Connecting to destination SFTP: {host}:{port} as {username}")

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = os.path.join(remote_dir, os.path.basename(file_path)).replace('\\', '/')
        sftp.put(file_path, remote_path)

        logger.info(f"Uploaded file to Kubra SFTP: {remote_path}")

        sftp.close()
        transport.close()

    except Exception as e:
        logger.error(f"Failed to send file to Kubra SFTP: {e}")
        raise


# %%
#############################
# 
# Run the Process
#
#############################

logger.info('Program Started')

try:
    vp_file = fetch_latest_vp_file_from_sftp()
    send_file_to_kubra(vp_file)

    subject = f"{programName} - VertexOne Letter File Transferred Successfully"
    body = (
        f"A file named '<b>{os.path.basename(vp_file)}</b>' was successfully transferred:<br>"
        f"- Pulled from Vertex SFTP<br>"
        f"- Saved locally to {os.getenv('LOCAL_SAVE_PATH')}<br>"
        f"- Sent to Kubra SFTP in {os.getenv('DEST_SFTP_PATH')}<br><br>"
        f"Program completed on {formattedDate}."
    )


    sendToDistributionList(subject, body, dl_list)
    logger.info("Success email sent.")

except Exception as e:
    logger.error(f"Fatal error occurred: {e}")
    subject = f"{programName} - VertexOne Letter File Transfer FAILED"
    body = f"The following error occurred during execution:\n\n{e}\n\nPlease check the logs for details."
    sendToDistributionList(subject, body, dl_list)

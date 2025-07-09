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
import gnupg
from dotenv import load_dotenv

# Load environment variables
with open('.env', 'r') as envFile:
    load_dotenv(stream=envFile)

gpg = gnupg.GPG(
     gnupghome=os.getenv('GPG_DIRECTORY'),
    gpgbinary=os.getenv('GPG_BINARY')
)

# Initialize Keeper Secrets Manager
from keeper_secrets_manager_core import SecretsManager
from keeper_secrets_manager_core.storage import FileKeyValueStorage

secrets_manager = SecretsManager(
    config=FileKeyValueStorage(os.getenv('KSM_CONFIG'))
)

# Retrieve VERTEX SFTP credentials from Keeper
vertex_sftp_secrets = secrets_manager.get_secrets(['wJL5RIc8DbdQLkXG0i_O5Q'])[0]
vertex_user = vertex_sftp_secrets.field('login', single=True)
vertex_pass = vertex_sftp_secrets.field('password', single=True)

# Retrieve Kubra SFTP credentials from Keeper
kubra_sftp_secrets = secrets_manager.get_secrets(['-b-qnRXophRlB5e6GdVoWA'])[0]
kubra_user = kubra_sftp_secrets.field('login', single=True)
kubra_pass = kubra_sftp_secrets.field('password', single=True)

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
# Function: Tracking Last Run
#
#############################

LAST_RUN_FILE = os.path.join(programDirectory, 'last_run_timestamp.txt')

def get_last_run_time():
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            content = f.read().strip()
            if content:
                try:
                    return datetime.datetime.fromisoformat(content)
                except ValueError:
                    logger.warning(f"Invalid timestamp in {LAST_RUN_FILE}: '{content}', skipping file processing.")
            else:
                logger.warning(f"{LAST_RUN_FILE} is empty, skipping file processing.")
    else:
        logger.info(f"{LAST_RUN_FILE} does not exist, skipping file processing.")
    
    # Default fallback
    return None


def set_last_run_time(timestamp=None):
    if not timestamp:
        timestamp = datetime.datetime.now()
    with open(LAST_RUN_FILE, 'w') as f:
        f.write(timestamp.isoformat())


# %%
#############################
# 
# Function: Get Most Recent VP_ File from VertexOne SFTP
#
#############################

def fetch_new_vp_files_from_sftp():
    try:
        host = os.getenv('SRC_SFTP_HOST')
        port = int(os.getenv('SRC_SFTP_PORT', 22))
        username = vertex_user
        password = vertex_pass
        logger.info(f"Connecting to source SFTP: {host}:{port} as {username}")

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        file_list = sftp.listdir_attr('.')
        vp_files = [f for f in file_list if f.filename.startswith('VP_') and f.filename.endswith('.zip')]

        if not vp_files:
            logger.info("No VP_ zip files found on SFTP.")
            return []

        last_run = get_last_run_time()
        if last_run is None:
            logger.warning("Last run timestamp is unavailable. Skipping file processing.")
            return []

        logger.info(f"Last run time: {last_run.isoformat()}")
        new_files = [f for f in vp_files if datetime.datetime.fromtimestamp(f.st_mtime) > last_run]


        if not new_files:
            logger.info("No new VP_ files found since last run.")
            return []

        local_dir = os.getenv('LOCAL_SAVE_PATH')
        os.makedirs(local_dir, exist_ok=True)

        downloaded_paths = []

        for f in new_files:
            remote_name = f.filename
            local_path = os.path.join(local_dir, remote_name)
            sftp.get(remote_name, local_path)
            downloaded_paths.append(local_path)
            logger.info(f"Downloaded: {remote_name} -> {local_path}")

        sftp.close()
        transport.close()

        return downloaded_paths

    except Exception as e:
        logger.error(f"Error during SFTP transfer: {e}")
        raise
# %%
#############################
# 
# Function: Send Files to Kubra SFTP
#
#############################

def send_file_to_kubra(file_path):
    try:
        host = os.getenv('DEST_SFTP_HOST')
        port = int(os.getenv('DEST_SFTP_PORT', 22))
        username = kubra_user
        password = kubra_pass
        remote_dir = os.getenv('DEST_SFTP_PATH', '/')
        logger.info(f"Connecting to destination SFTP: {host}:{port} as {username}")

        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        remote_path = os.path.join(remote_dir, os.path.basename(file_path)).replace('\\', '/')
        sftp.put(file_path, remote_path)

        logger.info(f"Uploaded encrypted file to Kubra SFTP: {remote_path}")

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
    downloaded_files = fetch_new_vp_files_from_sftp()

    encrypted_files = []

    for file_path in downloaded_files:
        output_path = file_path + '.gpg'
        with open(file_path, 'rb') as f:
            status = gpg.encrypt_file(
                f,
                recipients=['Kubra <it@kubra.com>'],
                output=output_path
            )

        if status.ok:
            logger.info(f"Encrypted {file_path} -> {output_path}")
            send_file_to_kubra(output_path)
            encrypted_files.append(output_path)
        else:
            logger.error(f"GPG encryption failed for {file_path}: {status.stderr}")

    if encrypted_files:
        subject = f"{programName} - {len(encrypted_files)} File(s) Encrypted & Transferred"
        file_list_html = "<br>".join([os.path.basename(f) for f in encrypted_files])
        body = (
            f"The following file(s) were encrypted and transferred to Kubra:<br>"
            f"{file_list_html}<br><br>"
            f"Saved to: {os.getenv('DEST_SFTP_PATH')}<br>"
            f"Completed on {formattedDate}."
        )
        set_last_run_time()
        sendToDistributionList(subject, body, dl_list)
        logger.info("Success email sent.")
    else:
        logger.info("No new files encrypted or transferred; skipping email.")

except Exception as e:
    logger.error(f"Fatal error occurred: {e}")
    subject = f"{programName} - VertexOne File Transfer FAILED"
    body = f"The following error occurred during execution:\n\n{e}\n\nPlease check the logs for details."
    sendToDistributionList(subject, body, dl_list)

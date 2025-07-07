#  VertexOne to Kubra SFTP Transfer

##  Overview

This Python script automates the process of transferring the most recent `VP_` file from the VertexOne SFTP site to the Kubra SFTP site. It performs the following:

- Connects securely to VertexOne’s SFTP
- Downloads the most recent file that begins with `VP_`
- Renames the file with a timestamp for uniqueness
- Uploads the file to Kubra’s SFTP location
- Logs all activity
- Sends success/failure notifications via email to a distribution list

---

##  Prerequisites

- Python 3.8+
- Access to both SFTP credentials (VertexOne + Kubra)
- Installed Python packages: `paramiko`, `python-dotenv`
- `.env` file configured with secure credentials (see below)

---

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jmcginnes/VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON.git
cd vertex-to-kubra-sftp

```
2. Install Dependencies

3. Configure Your Environment

Fill in your .env file like this:

```bash
# Shared libraries and config
SHARED_LIBRARIES=E:\cayenta\VersantPowerApps\SharedLibraries
KSM_CONFIG=E:\cayenta\VersantPowerApps\SharedLibraries\ksm-config.json

# Email Distribution List
DL=example@versantpower.com

# Program Info
PROGRAM_NAME=VERTEXONE_193H_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON

# Source SFTP (VertexOne)
SRC_SFTP_HOST=msftp.vertexgroup.com
SRC_SFTP_PORT=22
SRC_SFTP_USER=your_vertex_user (in Keeper)
SRC_SFTP_PASSWORD=your_vertex_password (in Keeper)

# Destination SFTP (Kubra)
DEST_SFTP_HOST=ftp-usa.kubra.com
DEST_SFTP_PORT=22
DEST_SFTP_USER=your_kubra_user (in Keeper)
DEST_SFTP_PASSWORD=your_kubra_password (in Keeper)
DEST_SFTP_PATH=/preptokubra/ 

# Local save path
LOCAL_SAVE_PATH=E:\cayenta\VersantPowerApps\Reports\JM_VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON\archive

```
4. Run the Script
```bash
python main.py
```
 
## Email Notifications
The script uses your internal O365Manager module to send emails to the recipients in the DL list. Emails are sent on both success and failure events.

## Setting Up Windows Task Scheduler
To run this automatically on a schedule:

Steps:
Open Task Scheduler

Click Create Task

Under General:

Name: VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON

Check Run whether user is logged in or not 

Check Run with Highest Privilege

Be sure to run as the svc_cayenta service account user, NOT your own username.

Triggers:

Add a trigger for Daily/Weekly at your desired time

Actions:

Action: Start a program

Program/script: "E:\programs\Python311-32\python.exe"

Add arguments: E:\cayenta\VersantPowerApps\Reports\JM_VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON\main.py

Start in: E:\cayenta\VersantPowerApps\Reports\JM_VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON

Settings:

Check: "Run task as soon as possible after a scheduled start is missed"

Click OK, enter the Windows password for the svc_cayenta service account when prompted.

## Security Notes
NEVER commit your .env file with real credentials.

## Maintainers
Name: John McGinnes

Team: CIS Team

License
Internal use only. Do not redistribute without company approval.

#  VertexOne to Kubra SFTP Transfer

##  Overview

This Python script automates the secure transfer of VertexOne "VP_" letter files to Kubra’s SFTP site. It performs the following steps:

Connects securely to VertexOne’s SFTP via credentials stored in Keeper Secrets Manager

Downloads all new VP_*.zip files since the last run

Encrypts each file using GPG

Renames each with a timestamp to ensure uniqueness

Uploads encrypted files to Kubra’s SFTP (also via Keeper credentials)

Logs all activity

Sends email notifications (success or failure) using O365

---

##  Prerequisites

Python 3.11+ (64-bit recommended)

Keeper Secrets Manager configured for the service account

GPG installed and configured

Python packages:

paramiko

python-dotenv

python-gnupg

keeper-secrets-manager-core

A configured .env file (see below) for non-secret settings

---

##  Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jmcginnes/VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON.git
cd VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON

```
2. Install Dependencies

3. Configure Your Environment

Fill in your .env file like this:

```bash
# Shared library and Keeper config
SHARED_LIBRARIES=E:\cayenta\VersantPowerApps\SharedLibraries
KSM_CONFIG=E:\cayenta\VersantPowerApps\SharedLibraries\ksm-config.json

# GPG encryption settings
GPG_DIRECTORY=E:\cayenta\GPG_Home
GPG_BINARY=C:\Program Files (x86)\GNU\GnuPG\gpg.exe
GPG_RECIPIENT=KubraPublicKey

# Email Distribution List
DL=jmcginnes@versantpower.com

# Program metadata
PROGRAM_NAME=VERTEXONE_193H_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON

# SFTP settings (host and port only)
SRC_SFTP_HOST=msftp.vertexgroup.com
SRC_SFTP_PORT=22
DEST_SFTP_HOST=ftp-usa.kubra.com
DEST_SFTP_PORT=22
DEST_SFTP_PATH=/preptokubra/

# Archive location for processed files
LOCAL_SAVE_PATH=E:\cayenta\VersantPowerApps\Reports\JM_VERTEXONE_LETTERS_TO_KUBRA_VIA_SFTP_PYTHON\archive

```
This script pulls sensitive credentials from Keeper Secrets Manager, not from .env.

These are referenced in the code and should be assigned to the correct secret in your Keeper vault. The script expects each to have:


4. Run the Script
```bash
python main.py
```
 
## Email Notifications
This script uses your internal O365Manager module to send status emails to the distribution list (DL). You'll receive messages when:

Files are successfully sent to Kubra

The process encounters a failure

No new files were found since last run (no email is sent)

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

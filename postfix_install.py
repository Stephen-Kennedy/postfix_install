#!/usr/bin/python3
# Author: Stephen J Kennedy
# Version 1.0 
# Script to setup Postfix on Ubuntu with Gmail SMTP relay

import os
import subprocess
import getpass

LOG_FILE = "/var/log/postfix_setup.log"

def run_command(command, sudo=False):
    """Run shell command securely and log output."""
    try:
        if sudo:
            command.insert(0, 'sudo')
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
        )
        with open(LOG_FILE, "a") as log:
            log.write(f"Command executed successfully: {' '.join(command)}\n")
            log.write(result.stdout.strip() + "\n")
        print(f"Command executed successfully: {' '.join(command)}")
        print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        with open(LOG_FILE, "a") as log:
            log.write(f"\nERROR: Command failed: {' '.join(command)}\n")
            log.write(f"Exit Code: {e.returncode}\n")
            log.write(f"Error Message: {e.stderr.strip()}\n")
        print(f"\nERROR: Command failed: {' '.join(command)}")
        print(f"Exit Code: {e.returncode}")
        print(f"Error Message: {e.stderr.strip()}")
        exit(1)
    except FileNotFoundError:
        with open(LOG_FILE, "a") as log:
            log.write(f"\nERROR: Command not found: {' '.join(command)}\n")
        print(f"\nERROR: Command not found: {' '.join(command)}")
        exit(1)

def preconfigure_postfix():
    """Preconfigure Postfix to avoid interactive prompts."""
    preconfig_data = "postfix postfix/main_mailer_type select Internet Site\n" \
                   "postfix postfix/mailname string localhost"
    try:
        process = subprocess.Popen(
            ["sudo", "debconf-set-selections"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(input=preconfig_data)
        if process.returncode != 0:
            print(f"ERROR: Preconfiguring Postfix failed: {stderr.strip()}")
            exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run preconfiguring command: {e}")
        exit(1)

def main():
    print("Postfix Gmail SMTP Relay Setup")
    print("================================")
    print(f"Logs will be written to {LOG_FILE}")

    # Get user input for Gmail account and password
    gmail_user = input("Enter your Gmail address: ").strip()
    gmail_password = getpass.getpass("Enter your Gmail App Password: ").strip()

    # Preconfigure Postfix to avoid interactive prompts
    print("\nPreconfiguring Postfix...")
    preconfigure_postfix()

    # Install Postfix if not installed
    print("\nInstalling Postfix...")
    run_command(["apt-get", "update"], sudo=True)
    run_command(["apt-get", "install", "postfix", "-y"], sudo=True)

    # Configure Postfix main.cf
    print("\nConfiguring Postfix...")
    postfix_config = """relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
"""

    try:
        with open("/tmp/main.cf", "w") as f:
            f.write(postfix_config)
        print("Postfix configuration file created successfully.")
    except Exception as e:
        print(f"\nERROR: Failed to write Postfix configuration file: {e}")
        exit(1)

    run_command(["mv", "/tmp/main.cf", "/etc/postfix/main.cf"], sudo=True)

    # Create Gmail authentication file
    print("\nCreating Gmail authentication file...")
    try:
        with open("/tmp/sasl_passwd", "w") as f:
            f.write(f"[smtp.gmail.com]:587 {gmail_user}:{gmail_password}\n")
        print("Gmail authentication file created successfully.")
    except Exception as e:
        print(f"\nERROR: Failed to write Gmail authentication file: {e}")
        exit(1)

    run_command(["mv", "/tmp/sasl_passwd", "/etc/postfix/sasl_passwd"], sudo=True)
    run_command(["chmod", "600", "/etc/postfix/sasl_passwd"], sudo=True)
    run_command(["postmap", "/etc/postfix/sasl_passwd"], sudo=True)

    # Restart Postfix
    print("\nRestarting Postfix...")
    run_command(["systemctl", "restart", "postfix"], sudo=True)

    print("\nPostfix setup is complete. Test by sending an email.")

if __name__ == "__main__":
    main()

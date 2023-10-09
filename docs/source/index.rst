PKI-Playground Documentation
==============================

Introduction
------------

This is the documentation for a Python 3 script that is used to generate self-signed certificates. The script is named `pki-playground.py`, and this documentation explains its usage and functionality.

Usage
-----

To use `pki-playground.py`, you can run it from the command line as follows.

First of all you need to unlock the repository, to get access to the generated files:

        sudo apt-get update && apt-get install git-crypt
        sudo python3 pki-playground.py --unlock KEY

This command will decrypt the shipped with this repository git-crypt key and
unlock the pkis/ directory.

After this, you need to initialize the PKI toolchain by entering the following command:

        sudo python3 pki-playground.py --pki-init PKI_NAME 

This will initialize the root CA/CN with the provided PKI_NAME.

To create the server certificates, you need to explicitly specify the root
certificates(PKI) name as follows:

        sudo python3 pki-playground.py --create-server-cert PKI_NAME DOMAIN_NAME 
   
This will create the server certificates that are based on the PKI with the provided name.

After that, you need to create the so-called deployment, which is a docker-compose file and 
the text, that will be temoparily added to the /etc/hosts file.
To do this, type as follows:

        sudo python3 pki-playground.py --create-deployment DEPLOYMENT_NAME HTTPS_PORT PKI_NAME DOMAIN_NAME 

This will initialise the deployments/DEPLOYMENT_NAME directory in the root of the repository,
and create docker-compose.yaml and the host_additions files.

To execute the deployment proceed with the following commands:

        sudo python3 pki-playground.py --start-deployment DEPLOYMENT_NAME

This will initialize the deployment. After that you can locate to the https://DOMAIN_NAME:HTTPS_PORT
and enjoy the secured connection made by the self-signed certificates.

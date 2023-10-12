![pylint](https://img.shields.io/badge/pylint-9.93-yellow?logo=python&logoColor=white)

# PKI-Playground README.md

## Introduction
This is the documentation for a Python 3 script that is used to generate self-signed certificates. 
The script is named `pki_playground.py`, and this documentation explains its usage and functionality.

## Usage
To use `pki_playground.py`, you can run it from the command line as follows.

### Unlocking the repository
The ./pkis directory in this repository is locked by default via git-crypt.
The key for the git-crypt is by default encrypted with AES-256 algorithm.

To get access this repository type as follows:
```shell
sudo apt-get update && apt-get install git-crypt
sudo python3 pki_playground.py --unlock KEY
```

This command will decrypt the shipped with this repository git-crypt key and
unlock the pkis/ directory.

## Setting up the docker environment
If you don't want to install the required packages on your host machine,
there's an option to build the docker environment:

```shell
$ docker build . -t sirin_pki_playground
$ ./docker-emit.sh
```

Will launch the interactive session in the docker container, and mount
the root of this repository.

### Initialing the PKI
After this, you need to initialize the PKI toolchain by entering the following command:
```shell
sudo python3 pki_playground.py --pki-init PKI_NAME 
```
This will initialize the root CA/CN with the provided name.


### Creating the server certificates(based on created PKI)
To create the server certificates, you need to explicitly specify the root
certificates(PKI) name as follows:
```shell
sudo python3 pki_playground.py --create-server-cert PKI_NAME DOMAIN_NAME
```
This will create the server certificates that are based on the PKI with the provided name.


### Managing deployments
After that, you need to create the so-called deployment, which is a docker-compose file and
the text, that will be temoparily added to the /etc/hosts file.
To do this, type as follows:
```shell
sudo python3 pki_playground.py --create-deployment DEPLOYMENT_NAME HTTPS_PORT PKI_NAME DOMAIN_NAME 
```

This will initialise the deployments/DEPLOYMENT_NAME directory in the root of the repository,
and create docker-compose.yaml and the host_additions files.

To execute the deployment proceed with the following commands:
```shell
sudo python3 pki_playground.py --start-deployment DEPLOYMENT_NAME
```

#!/usr/bin/env python3

"""
    This module provides an interface above the OpenSSL library,
    to generate the self-signed root and server CA/CN.
"""

import os
import sys
import subprocess
import argparse
import typing
import jinja2

# Contants
PKI_DIR = "pkis"
DEP_DIR = "deployments"
KEYSTORE_PASSWORD = None

# Arguments docstrings
ARG_PKI_INIT_HELP_MESSAGE = """
initialize the PKI with the specified name
"""

ARG_SRV_CRT_HELP_MESSAGE  = """
initalize the server certificates with the 
specified pki_name and domain_name
"""

ARG_CRT_DEP_HELP_MESSAGE  = """
create the deployment configuration using
the keystore password, https port, pki_name
and domain_name"""

ARG_STR_DEP_HELP_MESSAGE  = """
start the deployment: initialize the compose
routine and update /etc/hosts entry"""

ARG_REP_ULK_HELP_MESSAGE  = """
decrypt the AES-256 key and unlock this 
repository using the git-crypt utility"""


def executed_as_root() -> bool:
    """
    Check if this script running as root.

    :returns True when running as root, False when not
    """

    return os.geteuid() == 0


def _check_files(files: typing.List[str]) -> None:
    """
    Check if the provided files do exist in the filesystem

    :param: files: files to check
    :returns: None:
    """

    for file_path in files:
        if not os.path.isfile(file_path):
            print(f"Error: missing file {file_path}!")
            sys.exit(1)


def _parser_register_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Register the arguments in the arparse's argument parser.

    :param parser: argparse's argument parser class
    :returns: None
    """

    parser.add_argument(
        "--pki-init",
        metavar=("pki_name"),
        type=str,
        help=ARG_PKI_INIT_HELP_MESSAGE,
    )

    parser.add_argument(
        "--create-server-cert",
        metavar=("pki_name", "domain_name"),
        nargs=2,
        type=str,
        help=ARG_SRV_CRT_HELP_MESSAGE,
    )

    parser.add_argument(
        "--create-deployment",
        metavar=("deployment_name", "https_port", "pki_name", "domain_name"),
        nargs=4,
        help=ARG_CRT_DEP_HELP_MESSAGE,
    )

    parser.add_argument(
        "--start-deployment",
        metavar=("deployment_name"),
        type=str,
        help=ARG_STR_DEP_HELP_MESSAGE,
    )

    parser.add_argument(
        "--unlock",
        metavar=("key"),
        type=str,
        help=ARG_REP_ULK_HELP_MESSAGE
    )


def _generate_root_certs(pki_name: str) -> None:
    """
    Generate initial root certificates, using the provided pki_name
    variable. Create the folder with the same name as provided pki_name
    and push all the generated files into it.

    We are generating the .csr files using the csr_template.j2 that is
    in the pkis/ foler, so feel free to edit it.

    :param domain_name: name of the pki for the root certificate.
    :returns: None
    """

    # Create the root CA/CN directory
    working_directory = f"./{os.path.join(PKI_DIR, pki_name)}"
    print(f"Generating root certificates at {working_directory}")

    if not os.path.exists(working_directory):
        os.mkdir(working_directory)
    else:
        print(f"Error: PKI with the name {pki_name} already exists")
        sys.exit(1)

    # Generate root privatekey and certificate
    openssl_root_command = [
        "openssl",
        "req",
        "-x509",
        "-sha256",
        "-days",
        "356",
        "-nodes",
        "-newkey",
        "rsa:2048",
        "-subj",
        f"/CN={pki_name}.com/C=UA/L=Kiev",
        "-keyout",
        f"{pki_name}.key",
        "-out",
        f"{pki_name}.crt",
    ]
    subprocess.run(
        openssl_root_command,
        cwd=working_directory,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    # Generate private key
    openssl_genrsa_command = [
        "openssl",
        "genrsa",
        "-out",
        f"private.{pki_name}.key",
        "2048",
    ]
    subprocess.run(
        openssl_genrsa_command,
        cwd=working_directory,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    # Generate csf conf using Jinja2 template
    template = None
    with open(f'{PKI_DIR}/csr_template.j2', "r", encoding="utf8") as jfile:
        template = jinja2.Template(jfile.read())

    with open(f"{working_directory}/csr.conf", "w", encoding="utf8") as file:
        file.write(template.render(PKI_NAME=pki_name))

    # Generate CSR request using private key
    openssl_gencsr_command = [
        "openssl",
        "req",
        "-new",
        "-key",
        f"private.{pki_name}.key",
        "-out",
        f"{pki_name}.csr",
        "-config",
        "csr.conf",
    ]
    subprocess.run(
        openssl_gencsr_command,
        cwd=working_directory,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    # Log the successfull ending of the subroutine
    print(f"Done generating root certificates at {working_directory}")


def _generate_server_certs(pki_name: str, server_domain: str) -> None:
    """
    Generate the server certificates using the _previously generated_
    root certificates, with the server_domain basename.

    :param pki_name: name of the previously created pki
    :param server_domain: domain name of the server
    :returns: None
    """

    # Create the server CA/CN directory
    pki_directory = os.path.join(PKI_DIR, pki_name)
    if not os.path.exists(pki_directory):
        print(
            f"Error: PKI directory with the name of {pki_name} does not exist")
        sys.exit(1)

    # Assert that root CA/CN do exist
    required_filenames = [
        f"./pkis/{pki_name}/private.{pki_name}.key",
        f"./pkis/{pki_name}/{pki_name}.crt",
        f"./pkis/{pki_name}/{pki_name}.csr",
        f"./pkis/{pki_name}/{pki_name}.key",
    ]
    _check_files(required_filenames)

    # Create the neccesarry directories
    server_directory = os.path.join(pki_directory, "servers")
    if not os.path.exists(server_directory):
        os.mkdir(server_directory)

    domain_directory = os.path.join(server_directory, server_domain)
    if not os.path.exists(domain_directory):
        os.mkdir(domain_directory)
        print(f"Error: {domain_directory} is already in use")

    working_directory = f"./{domain_directory}"
    print(f"Generating server certificates at {working_directory}")

    # Generate the cert.conf file
    cert_template = None
    with open('./pkis/cert_template.j2', encoding="utf8") as jfile:
        cert_template = jinja2.Template(jfile.read())

    with open(f"{domain_directory}/cert.conf", "w", encoding="utf8") as cert_conf:
        cert_conf.write(
            cert_template.render(
                SERVER_DOMAIN=server_domain))

    # Create SSL with self signed CA
    openssl_create_ssl = [
        "openssl",
        "x509",
        "-req",
        "-in",
        f"../../{pki_name}.csr",
        "-CA",
        f"../../{pki_name}.crt",
        "-CAkey",
        f"../../{pki_name}.key",
        "-subj", 
        f"/C=UA/ST=Kiev Oblast/L=Something/O=Something Corp/OU=IT Dept/CN={server_domain}",
        "-CAcreateserial",
        "-out",
        f"{server_domain}.crt",
        "-days",
        "365",
        "-sha256",
        "-extfile",
        "cert.conf",
    ]
    subprocess.run(
        openssl_create_ssl,
        cwd=working_directory,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    # Generate pkcs12 keystore
    keystore_password = input(
        "Enter the keystore password(at least 6 characters): ")

    openssl_create_pkcs12_keystore = [
        "openssl",
        "pkcs12",
        "-export",
        "-out",
        "keystore.pkcs12",
        "-passout",
        f"pass:{keystore_password}",
        "-inkey",
        f"../../private.{pki_name}.key",
        "-in",
        f"../../servers/{server_domain}/{server_domain}.crt",
        "-certfile",
        f"../../{pki_name}.crt",
        "-name",
        f"{server_domain}",
    ]
    subprocess.run(
        openssl_create_pkcs12_keystore,
        cwd=working_directory,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)

    openssl_convert_to_jks = [
        'keytool',
        '-importkeystore',
        '-srckeystore', 'keystore.pkcs12',
        '-srcstorepass', keystore_password,
        '-srcstoretype', 'pkcs12',
        '-srcalias', server_domain,
        '-deststoretype', 'jks',
        '-destkeystore', 'keystore.jks',
        '-deststorepass', keystore_password,
        '-destalias', server_domain
    ]
    subprocess.run(openssl_convert_to_jks, cwd=working_directory, check=True)

    # Clean up and move the keystore to the 'keys' folder
    subprocess.run(['rm', 'keystore.pkcs12'], cwd=working_directory, check=True)

    # Log the successfull ending of the subroutine
    print(f"Done generating server certificates at {working_directory}")


def _generate_deployment(
        deployment_name: str,
        https_port: str,
        pki_name: str,
        domain_name: str) -> None:
    """
    Generate the deployment configuration with the docker-compose.yaml file and
    host_addition file, which contents will be temporarily appended to the /etc/hosts
    file.

    :param deployment_name: name of the deployment config
    :param https_port: forwarded(from the container) HTTPS port.
    :returns: None
    """

    print(f"Generating the deployment {deployment_name}")

    deployment_path = os.path.join(DEP_DIR, deployment_name)
    print(f"Generating the new deployment at {deployment_path}")

    if not os.path.exists(deployment_path):
        os.mkdir(deployment_path)

    # Request the keystore password
    keystore_password = input("Enter the keystore password: ")

    # Generate the docker-compose file using Jinja2 template
    compose_template = None
    with open(f'{DEP_DIR}/docker-compose-template.j2', encoding="utf8") as jfile:
        compose_template = jinja2.Template(jfile.read())

    with open(f"{DEP_DIR}/{deployment_name}/docker-compose.yaml", "w", encoding="utf8") as file:
        file.write(
            compose_template.render(
                HTTPS_PORT_BIND=https_port,
                KEYSTORE_PASSWORD=keystore_password,
                PKI_NAME=pki_name,
                DOMAIN_NAME=domain_name))

    # Generate the host_additions file, that is an appendix to the /etc/host
    # file
    with open(f"{DEP_DIR}/{deployment_name}/host_additions", "w", encoding="utf8") as file:
        file.write(f"127.0.0.1    {domain_name}")

    print(f"Done generating the deployment {deployment_name}")


def _start_deployment(deployment_name: str) -> None:
    """
    Start the deployment. Temprorarily update the /etc/hosts
    and initialize the docker-compose routine.

    :returns: None
    """

    print(f"Starting the deployment {deployment_name}")

    working_dir = os.path.join(DEP_DIR, deployment_name)
    if not os.path.exists(working_dir):
        print("Provided deployment does not exists")

    required_filenames = [
        f"{working_dir}/docker-compose.yaml",
        f"{working_dir}/host_additions",
    ]
    _check_files(required_filenames)

    # Add the deployment entry to the /etc/hosts
    hosts_entry = "#(fj)"

    with open(f"{working_dir}/host_additions", "r", encoding="utf8") as host_additions:
        hosts_entry = host_additions.read()

    with open("/etc/hosts", "a", encoding="utf8") as hosts:
        hosts.write(f"\n{hosts_entry}")

    # Launch the compose routine
    # On end, delete the deployment entry from the /etc/hosts file
    try:
        subprocess.run(["docker-compose", "up"], cwd=working_dir, check=True)
    except KeyboardInterrupt:
        with open("/etc/hosts", "r", encoding="utf8") as hosts:
            with open("/etc/hosts.tmp", "w", encoding="utf8") as temp_hosts:
                for line in hosts:
                    if hosts_entry not in line:
                        temp_hosts.write(line)
        subprocess.run(["mv", "/etc/hosts.tmp", "/etc/hosts"], check=True)

    print(f"Done starting the deployment {deployment_name}")


def _git_crypt_unlock(key: str) -> None:
    """
    Unlock the repository using the provided AES256 key.

    :param: key: key to decrypt the git-crypt key
    :returns: None
    """

    print("Unlocking the repository...")

    openssl_decrypt_aes256 = [
        "openssl",
        "enc",
        "-in",
        "git-crypt-key.enc",
        "-out",
        "git-crypt-key",
        "-d",
        "-aes256",
        "-pass",
        f"pass:{key}",
        "-pbkdf2"
    ]

    try:
        subprocess.run(openssl_decrypt_aes256, check=True)
        subprocess.run(["git-crypt", "unlock", "./git-crypt-key"], check=False)
    except subprocess.CalledProcessError:
        subprocess.run(["rm", "git-crypt-key"], check=False)
        print("Error: Unlocking failed")


def _handle_cli_arguments(args: typing.Any) -> None:
    """
    Handle the CLI arguments, that are passed to this script.

    :param args: args object that is produces by the argpare's parser
    :returns: None
    """

    if args.pki_init:
        _generate_root_certs(args.pki_init)

    if args.create_server_cert:
        pki_name, server_domain = args.create_server_cert
        _generate_server_certs(pki_name, server_domain)

    if args.create_deployment:
        deployment_name, https_port, pki_name, domain_name = args.create_deployment
        _generate_deployment(
            deployment_name,
            https_port,
            pki_name,
            domain_name)

    if args.start_deployment:
        _start_deployment(args.start_deployment)

    if args.unlock:
        _git_crypt_unlock(args.unlock)


def handle_cli_arguments() -> None:
    """
    Parse the arguments that are pumped to this script
    on execution.

    :returns: None
    """

    parser = argparse.ArgumentParser(sys.argv[0])
    _parser_register_arguments(parser)

    args = parser.parse_args()
    _handle_cli_arguments(args)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Entrypoint of this script

    :returns: None
    """

    if not executed_as_root():
        print("This script must be running as root.")
        sys.exit(1)

    handle_cli_arguments()


if __name__ == "__main__":
    main()

#!/usr/bin/env bash

if [ "$(id -u)" -ne 0 ]; then
	echo "This script must be run as root."
	exit 1
fi

# Argument parsing
USAGE="$(basename "$0") [-h] [-d domain] [-p password] -- Program to apply the certificates to the jenkins docker container

Options:
	-h Display this help message
	-d Set the domain name
	-p Set the keystore password
"

if [ "$#" -lt 2 ] || [ "$#" -gt 5 ]; then
	echo "$USAGE"
	exit 1
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      echo "${USAGE}"
      exit 0
      ;;
    -d|--domain)
      DOMAIN_NAME="$2"
      shift 
      shift
      ;;
    -p|--password)
      KEYSTORE_PASSWORD="$2"
      shift 
      shift
      ;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

if [ ! -d ${CERTS_DIR} ]; then
	# Check if the CERTS_DIR exists
	echo "Warning: Unable to find certificated directory"
	
	while true; do
		read -p "Do you want to create the empty certificates/ directory?[yN]: " yn
    		case $yn in
       		        [Yy]* ) mkdir -p certificates; break;;
        		[Nn]* ) exit 1;;
			* ) exit 1;;
    		esac
	done
fi
cd certificates

# Generate root private key and certificate
openssl req -x509 -sha256 -days 356 -nodes -newkey rsa:2048 -subj "/CN=${DOMAIN_NAME}/C=UA/L=Kiev" -keyout rootca.key -out rootca.crt

# Generate private key 
openssl genrsa -out ${DOMAIN_NAME}.key 2048

# Generate csf conf
cat > csr.conf << EOF
[ req ]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C = UA
ST = Kiev Oblast'
L = Kiev
O = ??
OU = ??
CN = ${DOMAIN_NAME}

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = ${DOMAIN_NAME}
DNS.2 = www.${DOMAIN_NAME}
IP.1 = 127.0.0.1
IP.2 = 127.0.0.1
EOF

# Generate CSR request using private key
openssl req -new -key ${DOMAIN_NAME}.key -out ${DOMAIN_NAME}.csr -config csr.conf

# Generate an external config file for the certificate
cat > cert.conf <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN_NAME}
EOF
# Create SSL with self signed CA
openssl x509 -req -in ${DOMAIN_NAME}.csr -CA rootca.crt -CAkey rootca.key -CAcreateserial -out ${DOMAIN_NAME}.crt -days 365 -sha256 -extfile cert.conf
cd ..

# Generate pkcs12 keystore
CERTS_DIR=certificates

openssl pkcs12 -export -out jenkins.pkcs12 \
-passout "pass:${KEYSTORE_PASSWORD}" -inkey $CERTS_DIR/$DOMAIN_NAME.key \
-in $CERTS_DIR/$DOMAIN_NAME.crt -certfile $CERTS_DIR/rootca.crt -name test-jenkins.com

# Convert it to the jks keystore
keytool -importkeystore -srckeystore jenkins.pkcs12 \
-srcstorepass "${KEYSTORE_PASSWORD}" -srcstoretype pkcs12 \
-srcalias ${DOMAIN_NAME} -deststoretype jks \
-destkeystore jenkins.jks -deststorepass "${KEYSTORE_PASSWORD}" \
-destalias ${DOMAIN_NAME}

# Clean up && Push to the corresponding folder
cp jenkins.jks keys/ && rm jenkins.pkcs12

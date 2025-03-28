import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import uuid
import base64
import hashlib
import os

def generate_rsa_key_pair():
    """Generates an RSA key pair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,  # Adjust key size as needed
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def public_key_to_jwk(public_key, key_id):
    """Converts a public key to JWK format."""
    public_numbers = public_key.public_numbers()
    #print(public_numbers)
    jwk = {
        "kty": "RSA",
        "kid": key_id,
        "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).decode('utf-8').rstrip("="),
        "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).decode('utf-8').rstrip("="),
        "alg": "RS256",  # or another appropriate algorithm
        "use": "sig"
    }
    return jwk


def generate_jwks(num_keys=1):
    """Generates a JWKS (JSON Web Key Set)."""
    keys = []
    for _ in range(num_keys):
        key_id = str(uuid.uuid4())  # Generate a unique key ID
        private_key, public_key = generate_rsa_key_pair()

        # Export private key to PEM format (for signing JWTs)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        # Save private key to a file (VERY IMPORTANT: SECURE THIS FILE!)
        with open(f"private_key_{key_id}.pem", "wb") as f:
            f.write(private_pem)  # Corrected this line


        jwk = public_key_to_jwk(public_key, key_id)
        keys.append(jwk)

    jwks = {"keys": keys}
    return jwks


if __name__ == "__main__":
    jwks_data = generate_jwks(num_keys=2)  # Generate 2 keys in the JWKS
    with open("jwks.json", "w") as f:
        json.dump(jwks_data, f, indent=4)
    print("JWKS generated and saved to jwks.json")
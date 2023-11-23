"""Encryption module."""

# This is the buffer module from https://github.com/py-mine/mcproto v0.5.0,
# which is licensed under the GNU LESSER GENERAL PUBLIC LICENSE v3.0

from __future__ import annotations

__author__ = "ItsDrike"
__license__ = "LGPL-3.0-only"

import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateKey,
    RSAPublicKey,
    generate_private_key,
)


def generate_shared_secret() -> bytes:  # pragma: no cover
    """Generate a random shared secret for client.

    This secret will be sent to the server in :class:`~mcproto.packets.login.login.LoginEncryptionResponse` packet,
    and used to encrypt all future communication afterwards.

    This will be symmetric encryption using AES/CFB8 stream cipher. And this shared secret will be 16-bytes long.
    """
    return os.urandom(16)


def generate_verify_token() -> bytes:  # pragma: no cover
    """Generate a random verify token.

    This token will be sent by the server in :class:`~mcproto.packets.login.login.LoginEncryptionRequest`, to be
    encrypted by the client as a form of verification.

    This token doesn't need to be cryptographically secure, it's just a sanity check that
    the client has encrypted the data correctly.
    """
    return os.urandom(4)


def generate_rsa_key() -> RSAPrivateKey:  # pragma: no cover
    """Generate a random RSA key pair for server.

    This key pair will be used for :class:`~mcproto.packets.login.login.LoginEncryptionRequest` packet,
    where the client will be sent the public part of this key pair, which will be used to encrypt the
    shared secret (and verification token) sent in :class:`~mcproto.packets.login.login.LoginEncryptionResponse`
    packet. The server will then use the private part of this key pair to decrypt that.

    This will be a 1024-bit RSA key pair.
    """
    return generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend(),
    )


def encrypt_token_and_secret(
    public_key: RSAPublicKey,
    verification_token: bytes,
    shared_secret: bytes,
) -> tuple[bytes, bytes]:
    """Encrypts the verification token and shared secret with the server's public key.

    :param public_key: The RSA public key provided by the server
    :param verification_token: The verification token provided by the server
    :param shared_secret: The generated shared secret
    :return: A tuple containing (encrypted token, encrypted secret)
    """
    # Ensure both the `shared_secret` and `verification_token` are instances
    # of the bytes class, not any subclass. This is needed since the cryptography
    # library calls some C code in the back, which relies on this being bytes. If
    # it's not a bytes instance, convert it.
    if (
        type(verification_token) is not bytes  # noqa: E721
    ):  # we don't want isinstance
        verification_token = bytes(verification_token)
    if (
        type(shared_secret) is not bytes  # noqa: E721
    ):  # we don't want isinstance
        shared_secret = bytes(shared_secret)

    encrypted_token = public_key.encrypt(verification_token, PKCS1v15())
    encrypted_secret = public_key.encrypt(shared_secret, PKCS1v15())
    return encrypted_token, encrypted_secret


def decrypt_token_and_secret(
    private_key: RSAPrivateKey,
    verification_token: bytes,
    shared_secret: bytes,
) -> tuple[bytes, bytes]:
    """Decrypts the verification token and shared secret with the server's private key.

    :param private_key: The RSA private key generated by the server
    :param verification_token: The verification token encrypted and sent by the client
    :param shared_secret: The shared secret encrypted and sent by the client
    :return: A tuple containing (decrypted token, decrypted secret)
    """
    # Ensure both the `shared_secret` and `verification_token` are instances
    # of the bytes class, not any subclass. This is needed since the cryptography
    # library calls some C code in the back, which relies on this being bytes. If
    # it's not a bytes instance, convert it.
    if (
        type(verification_token) is not bytes  # noqa: E721
    ):  # we don't want isinstance
        verification_token = bytes(verification_token)
    if (
        type(shared_secret) is not bytes  # noqa: E721
    ):  # we don't want isinstance
        shared_secret = bytes(shared_secret)

    decrypted_token = private_key.decrypt(verification_token, PKCS1v15())
    decrypted_secret = private_key.decrypt(shared_secret, PKCS1v15())
    return decrypted_token, decrypted_secret

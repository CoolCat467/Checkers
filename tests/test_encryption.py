# This is the buffer module from https://github.com/py-mine/mcproto v0.5.0,
# which is licensed under the GNU LESSER GENERAL PUBLIC LICENSE v3.0

from __future__ import annotations

__author__ = "ItsDrike"
__license__ = "LGPL-3.0-only"

from typing import cast

from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from checkers.encryption import (
    decrypt_token_and_secret,
    deserialize_public_key,
    encrypt_token_and_secret,
    serialize_public_key,
)

_SERIALIZED_RSA_PRIVATE_KEY = b"""
-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBAMtRUQmRHqPkdA2K
F6fM2c8ibIPHYV5KVQXNEkVx7iEKS6JsfELhX1H8t/qQ3Ob4Pr4OFjgXx9n7GvfZ
gekNoswG6lnQH/n7t2sYA 6D+WvSix1FF2J6wPmpKriHS59TDk4opjaV14S4K4XjW
Gmm8DqCzgXkPGC2dunFb+1A8mdkrAgMBAAECgYAWj2dWkGu989OMzQ3i6LAic8dm
t/Dt7YGRqzejzQiHUgUieLcxFKDnEAu6GejpGBKeNCHzB3B9l4deiRwJKCIwHqMN
LKMKoayinA8mj/Y/ O/ELDofkEyeXOhFyM642sPpaxQJoNWc9QEsYbxpG2zeB3sPf
l3eIhkYTKVdxB+o8AQJBAPiddMjU8fuHyjKT6VCL2ZQbwnrRe1AaLLE6VLwEZuZC
wlbx5Lcszi77PkMRTvltQW39VN6MEjiYFSPtRJleA+sCQQDRW2e3BX6uiil2IZ08
tPFMnltFJpa 8YvW50N6mySd8Zg1oQJpzP2fC0n0+K4j3EiA/Zli8jBt45cJ4dMGX
km/BAkEAtkYy5j+BvolbDGP3Ti+KcRU9K/DD+QGHvNRoZYTQsIdHlpk4t7eo3zci
+ecJwMOCkhKHE7cccNPHxBRkFBGiywJAJBt2pMsu0R2FDxm3C6xNXaCGL0P7hVwv
8y9B51 QUGlFjiJJz0OKjm6c/8IQDqFEY/LZDIamsZ0qBItNIPEMGQQJALZV0GD5Y
zmnkw1hek/JcfQBlVYo3gFmWBh6Hl1Lb7p3TKUViJCA1k2f0aGv7+d9aFS0fRq6u
/sETkem8Jc1s3g==
-----END PRIVATE KEY-----
"""
RSA_PRIVATE_KEY = cast(
    RSAPrivateKey,
    load_pem_private_key(_SERIALIZED_RSA_PRIVATE_KEY, password=None),
)
RSA_PUBLIC_KEY = RSA_PRIVATE_KEY.public_key()
SERIALIZED_RSA_PUBLIC_KEY = bytes.fromhex(
    "30819f300d06092a864886f70d010101050003818d0030818902818100cb515109911ea3e4740d8a17a7ccd9cf226c83c7615e4a5505cd124571ee210a4ba26c7c42e15f51fcb7fa90dce6f83ebe0e163817c7d9fb1af7d981e90da2cc06ea59d01ff9fbb76b1803a0fe5af4a2c75145d89eb03e6a4aae21d2e7d4c3938a298da575e12e0ae178d61a69bc0ea0b381790f182d9dba715bfb503c99d92b0203010001",
)


def test_encrypt_token_and_secret() -> None:
    """Test encryption returns properly encrypted (decryptable) values."""
    verification_token = bytes.fromhex("da053623dd3dcd441e105ee5ce212ac8")
    shared_secret = bytes.fromhex(
        "95a883358f09cd5698b3cf8a414a8a659a35c4eb877e9b0228b7f64df85b0f26",
    )

    encrypted_token, encrypted_secret = encrypt_token_and_secret(
        RSA_PUBLIC_KEY,
        verification_token,
        shared_secret,
    )

    assert (
        RSA_PRIVATE_KEY.decrypt(
            encrypted_token,
            OAEP(MGF1(SHA256()), SHA256(), None),
        )
        == verification_token
    )
    assert (
        RSA_PRIVATE_KEY.decrypt(
            encrypted_secret,
            OAEP(MGF1(SHA256()), SHA256(), None),
        )
        == shared_secret
    )


def test_decrypt_token_and_secret() -> None:
    """Test decryption returns properly decrypted values."""
    encrypted_token = bytes.fromhex(
        "5541c0c0fc99d8908ed428b20c260795bec7b4041a4f98d26fbed383e8dba077eb53fb5cf905e722e2ceb341843e875508134817bcd3a909ac279e77ed94fd98c428bbe00db630a5ad3df310380d9274ed369cc6a011e7edd45cbe44ae8ad2575ef793b23057e4b15f1b6e3e195ff0921e46370773218517922fbb8b96092d88",
    )
    encrypted_secret = bytes.fromhex(
        "1a43782ca17f71e87e6ef98f9be66050ecf5d185da81445d26ceb5941f95d69d61b726d27b5ca62aed4cbe27b40fd4bd6b16b5be154a7b6a24ae31c705bc47d9397589b448fb72b14572ea2a9d843c6a3c674b7454cef97e2d65be36e0d0a8cc9f1093a19a8d52a5633a5317d19779bb46146dfaea7a690a7f080fb77d59c7f9",
    )

    assert decrypt_token_and_secret(
        RSA_PRIVATE_KEY,
        encrypted_token,
        encrypted_secret,
    ) == (
        bytes.fromhex("da053623dd3dcd441e105ee5ce212ac8"),
        bytes.fromhex(
            "95a883358f09cd5698b3cf8a414a8a659a35c4eb877e9b0228b7f64df85b0f26",
        ),
    )


def test_serialize_public_key() -> None:
    """Test serialize_public_key."""
    assert serialize_public_key(RSA_PUBLIC_KEY) == SERIALIZED_RSA_PUBLIC_KEY


def test_deserialize_public_key() -> None:
    """Test deserialize_public_key."""
    assert deserialize_public_key(SERIALIZED_RSA_PUBLIC_KEY) == RSA_PUBLIC_KEY

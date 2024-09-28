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

from checkers.encryption import encrypt_token_and_secret

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

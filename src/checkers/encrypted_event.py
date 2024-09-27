"""Encrypted Event - Encrypt and decrypt event data."""

# Programmed by CoolCat467

from __future__ import annotations

# Encrypted Event - Encrypt and decrypt event data.
# Copyright (C) 2024  CoolCat467
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__title__ = "Encrypted Event"
__author__ = "CoolCat467, ItsDrike, and Ammar Askar"
__version__ = "0.0.0"
__license__ = "GNU General Public License Version 3"


from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    CipherContext,
    algorithms,
    modes,
)

from checkers.network import NetworkEventComponent


class EncryptedNetworkEventComponent(NetworkEventComponent):
    """Encrypted Network Event Component."""

    __slots__ = (
        "cipher",
        "decryptor",
        "encryptor",
        "shared_secret",
    )

    def __init__(self, name: str) -> None:
        """Initialize Encrypted Network Event Component."""
        super().__init__(name)

        self.cipher: Cipher[modes.CFB8]
        self.encryptor: CipherContext
        self.decryptor: CipherContext
        self.shared_secret: bytes | None = None

    @property
    def encryption_enabled(self) -> bool:
        """Return if encryption is enabled."""
        return self.shared_secret is not None

    def enable_encryption(self, shared_secret: bytes) -> None:
        """Enable encryption for this connection, using the ``shared_secret``.

        After calling this method, the reading and writing process for this connection
        will be altered, and any future communication will be encrypted/decrypted there.

        :param shared_secret:
            This is the cipher key for the AES symmetric cipher used for the encryption.

            See :func:`checkers.encryption.generate_shared_secret`.
        """
        # Ensure the `shared_secret` is an instance of the bytes class, not any
        # subclass. This is needed since the cryptography library calls some C
        # code in the back, which relies on this being bytes. If it's not a bytes
        # instance, convert it.
        if type(shared_secret) is not bytes:
            shared_secret = bytes(shared_secret)

        self.shared_secret = shared_secret
        self.cipher = Cipher(
            algorithms.AES(shared_secret),
            modes.CFB8(shared_secret),
            backend=default_backend(),
        )
        self.encryptor = self.cipher.encryptor()
        self.decryptor = self.cipher.decryptor()

    async def write(self, data: bytes) -> None:
        """Write encrypted data to stream."""
        if self.encryption_enabled:
            data = self.encryptor.update(data)
        return await super().write(data)

    async def read(self, length: int) -> bytearray:
        """Read `length` encrypted bytes from stream.

        Can raise following exceptions:
            NetworkStreamNotConnectedError
            NetworkTimeoutError - Timeout or no data
        OSError - Stopped responding
        """
        data = await super().read(length)
        if self.encryption_enabled:
            return bytearray(self.decryptor.update(data))
        return data

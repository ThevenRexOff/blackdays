import json
import base64


class FwcimDecryptorAmazon:

    __XXTEA_DELTA = 0x9E3779B9
    __CRC32_POLYNOMIAL = 0xEDB88320

    __KNOWN_KEYS = {
        "ECdITeCs": [1888420705, 2576816180, 2347232058, 874813317]
    }

    def __init__(self) -> None:
        self.__crc32_table = self.__generate_crc32_table()

    #//! Public Methods ──────────────────────────────────────────
    def decrypt_md(self, md_value: str) -> dict:
        """
        Decrypt an Amazon FWCIM metadata value.
        
        Args:
            md_value: The encrypted md value (format: "KEY_ID:BASE64_DATA")
        
        Returns:
            Dictionary with decrypted data and validation info
        """
        try:
            # Split key identifier and encrypted data
            if ':' not in md_value:
                return {
                    'status': False,
                    'description': 'Invalid md format: missing key identifier'
                }
            
            key_id, encrypted_b64 = md_value.split(':', 1)
            
            # Get decryption key
            if key_id not in self.__KNOWN_KEYS:
                return {
                    'status': False,
                    'description': f'Unknown key identifier: {key_id}'
                }
            
            key = self.__KNOWN_KEYS[key_id]
            
            # Decrypt: Base64 → XXTEA decrypt
            encrypted = self.__base64_decode(encrypted_b64)
            decrypted = self.__xxtea_decrypt(encrypted, key)
            
            # Extract CRC32 and JSON (format: "crc32#json")
            if '#' not in decrypted:
                return {
                    'status': False,
                    'description': 'Invalid decrypted format: missing CRC32 separator'
                }
            
            crc32_hex, json_str = decrypted.split('#', 1)
            
            # Verify CRC32
            calculated_crc = self.__crc32(json_str)
            is_valid = (crc32_hex.lower() == calculated_crc.lower())
            
            # Parse JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                return {
                    'status': False,
                    'description': f'Invalid JSON in decrypted data: {str(e)}'
                }
            
            return {
                'status': True,
                'keyId': key_id,
                'crc32': crc32_hex,
                'calculated_crc32': calculated_crc,
                'valid': is_valid,
                'data': data,
                'context': 'Amazon FWCIM Metadata Decryptor',
                'poweredBy': 'Vxsilisk @ Sxgitario API Gateways Service'
            }
            
        except Exception as error:
            return {
                'status': False,
                'description': f'Decryption error: {str(error)}'
            }

    def add_key(self, key_id: str, key_material: list) -> None:
        """
        Add a new decryption key to the known keys.
        
        Args:
            key_id: Key identifier (e.g., "ECdITeCs")
            key_material: List of 4 integers representing the key
        """
        if len(key_material) != 4:
            raise ValueError("Key material must contain exactly 4 integers")
        self.__KNOWN_KEYS[key_id] = key_material

    #//! Private Methods - CRC32 ─────────────────────────────────
    def __generate_crc32_table(self) -> list:
        """Generate CRC32 lookup table."""
        table = []
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ self.__CRC32_POLYNOMIAL
                else:
                    crc >>= 1
            table.append(crc & 0xFFFFFFFF)
        return table

    def __crc32(self, data: str) -> str:
        """Calculate CRC32 checksum and return as hex string."""
        crc = 0xFFFFFFFF
        for char in data.encode('utf-8'):
            crc = self.__crc32_table[(crc ^ char) & 0xFF] ^ (crc >> 8)
        return format((crc ^ 0xFFFFFFFF) & 0xFFFFFFFF, '08x')

    #//! Private Methods - XXTEA Decryption ──────────────────────
    def __xxtea_decrypt(self, data: str, key: list) -> str:
        """
        XXTEA decryption implementation.
        Reverses the encryption from metadataGenSxgitario.py
        """
        if len(data) == 0:
            return ''

        # Convert string to 32-bit words
        n = len(data) // 4
        v = []
        for i in range(n):
            word = 0
            for j in range(4):
                idx = i * 4 + j
                if idx < len(data):
                    word |= ord(data[idx]) << (j * 8)
            v.append(word)

        # XXTEA decryption
        n = len(v)
        rounds = 6 + 52 // n
        total = (rounds * self.__XXTEA_DELTA) & 0xFFFFFFFF
        y = v[0]

        for _ in range(rounds):
            e = (total >> 2) & 3
            for p in range(n - 1, -1, -1):
                z = v[(p - 1) % n]
                mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((total ^ y) + (key[(p & 3) ^ e] ^ z))
                v[p] = (v[p] - mx) & 0xFFFFFFFF
                y = v[p]
            total = (total - self.__XXTEA_DELTA) & 0xFFFFFFFF

        # Convert words back to string
        result = []
        for word in v:
            for j in range(4):
                byte_val = (word >> (j * 8)) & 0xFF
                if byte_val != 0:  # Skip null padding
                    result.append(chr(byte_val))
        
        return ''.join(result)

    def __base64_decode(self, data: str) -> str:
        """Base64 decode a string."""
        return base64.b64decode(data).decode('latin-1')


# ────────────────────────────────────────────────────────────────────────
# 📝 EXAMPLE USAGE
# ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Example 1: Decrypt a metadata value
    decryptor = FwcimDecryptorAmazon()
    
    
    result = decryptor.decrypt_md("ECdITeCs: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")
    # print(result['data'])
    # save
    file = open('fingerprint_real.json', 'w')
    file.write(json.dumps(result['data'], indent=4))
    file.close()

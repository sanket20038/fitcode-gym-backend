from cryptography.fernet import Fernet

def generate_qr_encryption_key():
    key = Fernet.generate_key()
    print("Generated QR_ENCRYPTION_KEY:")
    print(key.decode())

if __name__ == "__main__":
    generate_qr_encryption_key()

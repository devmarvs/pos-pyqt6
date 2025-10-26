import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), stored_hash.encode('utf-8'))
    except Exception:
        # backward compatibility with old plaintext demo hashes
        return plain == stored_hash

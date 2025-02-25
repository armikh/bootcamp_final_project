from hashlib import sha256

secret = "quera_project".encode("utf-8")
secret_key = sha256(secret).hexdigest()
print(secret_key)
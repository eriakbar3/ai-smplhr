import redis

# Ganti sesuai alamat Redis kamu (bisa remote)
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

def set_value(key: str, value: str):
    r.set(key, value)

def get_value(key: str):
    return r.get(key)

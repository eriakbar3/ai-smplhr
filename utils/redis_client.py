import redis

# Ganti sesuai alamat Redis kamu (bisa remote)
r = redis.Redis(host='redis-19040.c278.us-east-1-4.ec2.redns.redis-cloud.com', port=19040, db=0, password='TkSrLYxc2nad2PlV6M4Q93UmNEllUmCQ', decode_responses=True)

def set_value(key: str, value: str):
    r.set(key, value)

def get_value(key: str):
    return r.get(key)

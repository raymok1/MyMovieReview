import redis

r = redis.Redis(
    host='redis-16105.c323.us-east-1-2.ec2.redns.redis-cloud.com',
    port=16105,
    decode_responses=True,
    username="default",
    password="Uyh3GwUscxJ6f7ivzCNERzYZo8OM7ep0",
)

success = r.set('name', 'kayla')
print(success)

result = r.get('name')
print(result)
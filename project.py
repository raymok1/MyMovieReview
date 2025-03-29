import redis
import tmdbsimple as tmdb

# Redis DB connection
r = redis.Redis(
    host='redis-16105.c323.us-east-1-2.ec2.redns.redis-cloud.com',
    port=16105,
    decode_responses=True,
    username="default",
    password="Uyh3GwUscxJ6f7ivzCNERzYZo8OM7ep0",
)


# TheMovieDb web API connection via tmdbsimple wrapper: https://github.com/celiao/tmdbsimple/
# tmdb.API_KEY = '854604cc4fd32fce5035a3fd5f61cfd7'
# movie = tmdb.Movies(603)
# print(movie.info())

# Login
login = False
print("Please login")
while login == False:
    username = input("Username: ")
    password = input("Password: ")

    db_username = r.get("username")
    db_password = r.get("password")

    if username == db_username and password == db_password:
        login = True

    if login == False:
        print("Incorrect username or password. Please try again.")


print("LOGGED in")
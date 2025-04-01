from abc import ABC, abstractmethod
import redis
import tmdbsimple as tmdb

# Component class
class Media(ABC):

    def __init__(self, id, title, release_date):
        self.id = id
        self.title = title
        self.release_date = release_date

    @abstractmethod
    def get_details(self):
        pass

# Concrete component class
class Movie(Media):

    def __init__(self, id, title, release_date):
        super.__init__(self, id, title, release_date)

    def get_details(self):
        return f"{self.id}\t{self.title}\t{self.release_date}"
    
# Abstract decorator class
class MovieDecorator(Movie, Media):
    def __init__(self, movie):
        self._movie = movie

    @abstractmethod
    def get_details(self):
        pass

# Concrete decorator class
class MovieReviewDecorator(MovieDecorator):
    def __init__(self, movie, rating, review):
        super.__init__(self, movie)
        self.rating = rating
        self.review = review

    def get_details(self):
        return self._movie.get_details() + f"\t{self.rating}\t{self.review}"

# Redis DB connection
r = redis.Redis(
    host = "redis-16105.c323.us-east-1-2.ec2.redns.redis-cloud.com",
    port = 16105,
    decode_responses = True,
    username = "default",
    password = "Uyh3GwUscxJ6f7ivzCNERzYZo8OM7ep0",
)

# TheMovieDb web API connection via tmdbsimple wrapper: https://github.com/celiao/tmdbsimple/
tmdb.API_KEY = "854604cc4fd32fce5035a3fd5f61cfd7"

# Login method
def login():
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

# Search for movie method
def movie_search():
    keyword = input("Search for a movie by title or keyword: ")
    search = tmdb.Search().movie(query = keyword)
    print("Id\tTitle\t\tRelease Date")
    for s in search["results"]:
        print(f"{s["id"]}\t{s["title"]}\t{s["release_date"]}")

    # Add movie to watchlist
    movie_id = input("Input the id of the movie you wish to select: ")
    movie = tmdb.Movies(movie_id).info()
    print(f"You have selected '{movie["title"]}'")
    add_to_watchlist = input("Would you like to add this movie to your watchlist? Y or N: ")

    if add_to_watchlist == "Y" or add_to_watchlist == "y":
        print("add movie to watchlist")
    elif add_to_watchlist == "N" or add_to_watchlist == "n":
        print("go back to main menu")

# View watchlist function
def view_watchlist():
    watchlist = r.smembers("watchlist")
    print(watchlist)

    print("Id\tTitle\t\tRelease Date")
    for id in watchlist:
        movie = tmdb.Movies(id).info()
        print(f"{movie["id"]}\t{movie["title"]}\t{movie["release_date"]}")

    print("Actions:\n1. Delete movie from watchlist\n2. Add movie to watchlist\n3. Back to main menu")
    action = input("Which action would you like to do? ")

    if action == 1:
        print("Which movie would you like to delete?")
        movie_id = input("Type the movie ID here: ")
    elif action == 2:
        pass
        # Go to movie search feature
    elif action == 3:
        pass
        # Go to main menu

# Main method
print("here")
from abc import ABC, abstractmethod
import redis
import tmdbsimple as tmdb
import datetime
from queue import Queue


# SINGLETON DESIGN PATTERN - This design pattern is used to create a logger. This design 
# pattern was used so only one instance of the logger is created, and this instance can be 
# accessed from any class.    

# Logger class 
class Logger:
    _instance = None

    def __init__(self):
        self._logs = ""

    @staticmethod
    def get_instance():
        if Logger._instance is None:
            Logger._instance = Logger()
        return Logger._instance
    
    def log(self, message):
        self._logs += f"{datetime.datetime.now(datetime.timezone.utc)} {message}\n"

    def log_debug(self, message):
        self._logs += f"{datetime.datetime.now(datetime.timezone.utc)} [DEBUG] {message}\n"

    def log_error(self, message):
        self._logs += f"{datetime.datetime.now(datetime.timezone.utc)} [ERROR] {message}\n"

    def get_logs(self):
        print(self._logs)


# DECORATOR DESIGN PATTERN - The following 4 classes are used in the decorator design pattern. 
# Although not necessary in this simple application, this design pattern was chosen for future 
# development when is may be necessary to add more "decorations" to media objects at runtime.

# Component class
class Media(ABC):

    def __init__(self, id, title, release_date):
        self.id = id
        self.title = title
        self.release_date = release_date
        logger = Logger.get_instance()
        logger.log_debug("Media object created")

    @abstractmethod
    def get_details(self):
        pass

# Concrete component class
class Movie(Media):

    def __init__(self, id, title, release_date):
        super().__init__(id, title, release_date)
        logger = Logger.get_instance()
        logger.log_debug("Movie object created")

    def get_details(self):
        return f"{self.id}\t{self.title}\t{self.release_date}"
    
# Abstract decorator class
class MovieDecorator(Movie, Media):
    def __init__(self, movie):
        self._movie = movie
        logger = Logger.get_instance()
        logger.log_debug("MovieDecorator object created")

    @abstractmethod
    def get_details(self):
        pass

# Concrete decorator class
class MovieReviewDecorator(MovieDecorator):
    def __init__(self, movie, rating, review):
        super().__init__(movie)
        self.rating = rating
        self.review = review
        logger = Logger.get_instance()
        logger.log_debug("MovieReviewDecorator object created")

    def get_details(self):
        return self._movie.get_details() + f"\t{self.rating}\t{self.review}"


# OBJECT POOL DESIGN PATTERN - This design pattern is used to manage a pool of database 
# connections. Each time a connect is needed, it is taken from the pool then released back 
# to the pool when it is no longer needed. If I had more time, I would switch to a SQL 
# database as Redis already uses the object pool pattern within its connection, so creating 
# one is redundant.

class DatabaseConnection:
    def __init__(self):
        self.connection = redis.Redis(
            host = 'redis-16105.c323.us-east-1-2.ec2.redns.redis-cloud.com',
            port = 16105,
            decode_responses = True,
            username = "default",
            password = "Uyh3GwUscxJ6f7ivzCNERzYZo8OM7ep0",
        )

    def get_connection(self):
        return self.connection
        
    def close(self):
        self.connection.close()

class DbConnectionPool:
    def __init__(self, max_connections):
        self.pool = Queue(maxsize = max_connections)
        self.max_connections = max_connections

    def acquire(self):
        if self.pool.qsize() < self.max_connections:
            self.db_connection = DatabaseConnection().get_connection()
            self.pool.put(self.db_connection)
        else:
            self.db_connection = self.pool.get()
        return self.db_connection
    
    def release(self, db_connection):
        self.pool.put(db_connection)

    def close_all(self):
        while self.pool.empty() == False:
            db_connection = self.pool.get()
            db_connection.close()


# Create Redis DB connection from object pool
# For this simple app, I am using a maximum pool size of 2
r = DbConnectionPool(2).acquire()

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

    logger = Logger.get_instance()
    logger.log("User logged in")

# Search for movie method
def movie_search():
    keyword = input("Search for a movie by title or keyword: ")
    search = tmdb.Search().movie(query = keyword)
    
    movies = []
    for s in search["results"]:
        m = Movie(s["id"], s["title"], s["release_date"])
        movies.append(m)

    print("Id\tTitle\t\tRelease Date")
    for m in movies:
        print(m.get_details())

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
        m = tmdb.Movies(id).info()
        movie = Movie(m["id"], m["title"], m["release_date"])
        movie.get_details()

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

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
    def __init__(self, movie, review):
        super().__init__(movie, review)
        self.review = review
        logger = Logger.get_instance()
        logger.log_debug("MovieReviewDecorator object created")

    def get_details(self):
        return self._movie.get_details() + f"\t{self.review}"


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

def main_menu():
    print("\n" * 100)
    print("Welcome to MyMovieReview")
    print("Please choose from the menu options below:")
    print("1. Search for a movie")
    print("2. View watchlist")
    print("3. View my movie reviews")
    print("4. View app logs")
    print ("5. Exit app")

    choice = int(input("Type the number of the option you wish to choose: "))

    match choice:
        case 1:
            movie_search()
        case 2:
            view_watchlist()
        case 3:
            view_reviews()
        case 4:
            view_app_logs()
        case 5:
            pass

# Search for movie method
def movie_search():
    print("\n" * 100)
    keyword = input("Search for a movie by title or keyword: ")
    search = tmdb.Search().movie(query = keyword)
    
    movies = []
    for s in search["results"]:
        m = Movie(s["id"], s["title"], s["release_date"])
        movies.append(m)

    print("Id\tTitle\t\tRelease Date")
    for m in movies:
        print(m.get_details())

    # Select movie and action
    movie_id = input("\nInput the id of the movie you wish to select: ")
    m = tmdb.Movies(movie_id).info()
    movie = Movie(m["id"], m["title"], m["release_date"])
    
    print("\n" * 100)
    print(f"You have selected '{movie.title}'")
    print("What would you like to do?")
    print("1. Add this movie to watchlist")
    print("2. Review this movie")
    print("3. Return to main menu")
    choice = int(input("Type the number of the option you wish to choose: "))

    match choice:
        case 1:
            add_to_watchlist(movie.id)
        case 2:
            review_movie(movie)
        case 3:
            main_menu()

def add_to_watchlist(movie_id):
    r.sadd("watchlist", movie_id)
    print("\nMovie has been added to watchlist.")
    input("Press any key to continue to main menu.")
    main_menu()

def review_movie(movie):
    print(f"Type your review for {movie.title}:")
    review_text = input("Review Text: ")
    r.hset("reviews", movie.id, review_text)
    
    # This line is currently unused in the application but it just demonstrates how the 
    # decorator pattern is used to dynamically add properties to an existing object
    reviewed_movie = MovieReviewDecorator(movie, review_text)

    print("\nMovie review has been added.")
    input("Press any key to continue to main menu.")
    main_menu()

# View watchlist function
def view_watchlist():
    watchlist = r.smembers("watchlist")

    print("Id\tTitle\t\tRelease Date")
    for id in watchlist:
        m = tmdb.Movies(id).info()
        movie = Movie(m["id"], m["title"], m["release_date"])
        movie.get_details()

    print("What would you like to do?")
    print("1. Delete movie from watchlist")
    print("2. Return to main menu")
    choice = int(input("Type the number of the option you wish to choose: "))

    match choice:
        case 1:
            delete_from_watchlist(movie.id)
        case 2:
            main_menu()

def delete_from_watchlist(movie_id):
    r.srem("watchlist", movie_id)
    print("\nMovie has been removed from watchlist.")
    input("Press any key to continue to main menu.")
    main_menu()
    
def view_reviews():
    pass

def view_app_logs():
    logger = Logger.get_instance()
    logger.get_logs()

    input("Press any key to continue...")

# Main method
main_menu()

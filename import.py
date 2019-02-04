from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import pandas as pd
import os

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    data =pd.read_csv('books.csv')
    for isbn,title,author,year in zip(data.isbn,data.title,data.author,data.year):
        db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn,:title,:author,:year)", {"isbn":isbn,"title":title,"author":author,"year":year})
        print(f"Added book:[{isbn} , {title},  {author}, {year}] ")
    db.commit()


if __name__ == "__main__":
    main()

from bs4 import BeautifulSoup
import pickle
import requests
import json
import re
import os
from typing import Dict, List, Set
from pathlib import Path
import math


class BookSearch:
    API_KEY = "AIzaSyCPNlIirLI65ywNzl_C04hjo2Y3wzVGnGw"
    url = "https://www.googleapis.com/books/v1/volumes?key={}&startIndex={}&q=subject:{}"

    def search_books(self, genre: str, page: int) -> Dict:
        """Returns 10 books of specified genre and start index"""

        query = self.url.format(self.API_KEY, page * 10, genre)
        print(query)
        res = requests.get(query)
        books = res.json()

        items = books["items"]

        collected = []
        for book in items:
            collected.append({
                "title": book["volumeInfo"]["title"],
                "authors": book["volumeInfo"].get("authors"),
                "genre": genre,
                "language": book["volumeInfo"]["language"],
                "publishedDate": book["volumeInfo"].get("publishedDate"),
            })

        return collected, books["totalItems"]


class BookCrawler:
    # url = "https://libgen.li/index.php"
    # crawler configuration
    download_page_base_url: str = "https://libgen.rocks/{}"
    search_url: str = "https://libgen.li/index.php?req={}&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=25&filesuns=all"
    allowed_file_formats: Set[str] = {"pdf", "epub"}
    maximum_retries = 25
    progress_summary = {
        "file_formats": {file_format: 0 for file_format in allowed_file_formats},
        "downloaded": {},
    }

    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    table_columns = {"title": 0, "author": 1, "publisher": 2,
                     "year": 3, "language": 4, "pages": 5, "size": 6, "extension": 7, "mirrors": 8}

    def __init__(self, resume: bool = False) -> None:
        """Creates a crawler instance which loads the data about books
        into class and provides methods to download books
        """
        if resume:
            try:
                with open(f"{self.current_dir}\\progress.dat", "rb") as progress_file:
                    self.progress_summary = pickle.load(progress_file)
            except Exception as error:
                print(f"Error opening books json file : \n{error}")

    def get_book_results(self, book: Dict) -> Dict:
        """Takes book data in JSON format and returns the most relevant
        download page link for that book
        """
        try:
            # fetch search results
            author = ""
            if book.get("authors"):
                author = book["authors"][0]

            search_query = "+".join(
                f"{book['title']} {author}".split())
            print(f"Search Query = {search_query}")

            webpage = requests.get(self.search_url.format(search_query))
            soup = BeautifulSoup(webpage.content, "html.parser")
            print("Finished Parsing HTML response")

            table = soup.select("tbody tr")

            # fetch download links
            last_row = None
            for i in range(min(self.maximum_retries, len(table))):
                last_row = table[i]("td")
                file_format = last_row[self.table_columns["extension"]].text

                if file_format in self.allowed_file_formats:
                    break
            else:
                raise Exception("Couldn't find book in preferred file formats")

            if not last_row:
                raise Exception("No Results for this book.")

            download_page_link = last_row[self.table_columns["mirrors"]].select_one(
                "a[title=\"libgen\"]"
            )
            print(f"Download Page Link : {download_page_link['href']}")

            return {
                "json_data": book,
                "download_link": download_page_link["href"],
                "file_format": file_format
            }
        except Exception as error:
            if isinstance(error, requests.RequestException):
                print(f"Error occured when handling the request :\n{error}")
            else:
                print(f"Error while fetching download links :\n{error}")

            return {
                "json_data": book,
                "download_link": None,
                "file_format": None
            }

    def download_book(self, book: Dict) -> Dict:
        """Given a download page link, extracts the download link and
        downloads the book
        """
        try:
            download_page = requests.get(book["download_link"])
            soup = BeautifulSoup(download_page.content, "html.parser")

            download_link_anchor = soup.select_one("td a h2").parent
            download_link = self.download_page_base_url.format(
                download_link_anchor["href"]
            )
            print(f"Book Download Link : {download_link}")

            print("Downloading Book ...")
            res = requests.get(download_link, allow_redirects=True)

            print("Saving Book ...")
            filename = res.headers.get("content-disposition")
            filename = re.search(r"filename=\"(.+)\"", filename).group(1)
            print(filename)

            # create folder for each genre
            Path(f"{self.current_dir}\downloads\{book['json_data']['genre']}").mkdir(
                parents=True, exist_ok=True
            )
            with open(f"{self.current_dir}\downloads\{book['json_data']['genre']}\{filename}", "wb") as download:
                download.write(res.content)
            print("Finished Downloading Book!")

            return {"filename": filename, **book}
        except Exception as error:
            print(f"Error occurred when downloading book:\n{error}")

    def save_progress(self, book: Dict) -> int:
        print("Saving Progress ...")
        try:
            book_title = book["json_data"]["title"]
            book_genre = book["json_data"]["genre"]
            book_format = book["file_format"]

            if (temp := self.progress_summary["downloaded"].get(book_genre)):
                temp[book_title] = book
            else:
                self.progress_summary["downloaded"][book_genre] = {}
                self.progress_summary["downloaded"][book_genre][book_title] = book

            self.progress_summary["file_formats"][book_format] += 1

            with open(f"{self.current_dir}\\progress.dat", "wb") as progress_file:
                pickle.dump(self.progress_summary, progress_file)

            # print(self.progress_summary["downloaded"])
            return len(self.progress_summary["downloaded"][book_genre])
        except Exception as error:
            print(f"Error when saving progress :\n{error}")

    def print_summary(self) -> None:
        downloaded = self.progress_summary["downloaded"]
        formats = self.progress_summary["file_formats"]

        print("\n" * 3 + "-" * 50 + "\n")

        print(f"Downloaded {len(downloaded)} genres :")

        for i, (genre, books) in enumerate(downloaded.items()):
            print(f"\t{i+1}. {genre}")
            for i, (title, book) in enumerate(books.items()):
                print(f"\t\t{i+1}. {book['json_data']['title']}")
        print()

        print(f"In {len(formats)} file formats :")
        for file_type, count in formats.items():
            print(f"\t{file_type} : {count}")
        print()

        print("-" * 50 + "\n")


def download_genre(crawler, searcher, genre, total):
    for page in range(math.ceil(total / 10)):
        books, _ = searcher.search_books(genre, page)

        for book in books:
            book_result = crawler.get_book_results(book)
            if not book_result:
                print("Couldn't find a download link.\n\n")
                continue

            book_data = crawler.download_book(book_result)
            if not book_data:
                print("\n\n")
                continue

            count = crawler.save_progress(book_data)
            print(f"[{count}/{books_per_genre}]\n\n")

            if count == books_per_genre:
                return


if __name__ == "__main__":
    # get 10 books from google api
    # try to download them
    # repeat until 50 books have been collected for each genre
    # write the downloaded books to the json file
    print("Starting Crawler ...")

    genres = ["action", "romance", "horror", "mystery", "fiction"]
    books_per_genre = 50
    crawler = BookCrawler(resume=True)
    searcher = BookSearch()

    for genre in genres:
        _, total = searcher.search_books(genre, 0)

        print(f"total books in {genre} : {total}")

        download_genre(crawler, searcher, genre, total)

    crawler.print_summary()

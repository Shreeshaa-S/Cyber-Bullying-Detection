import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import PyPDF2


class TextExtractor:
    blacklist = ['[document]',   'noscript', 'header',
                 'html', 'meta', 'head', 'input', 'script']

    def pdf_to_text(self, pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfFileReader(pdf_file)
            page_count = pdf_reader.numPages

            output = ""
            for i in range(page_count):
                page = pdf_reader.getPage(i)
                output += page.extractText()

        return output

    def epub_to_html(self, epub_path):
        book = epub.read_epub(epub_path)
        chapters = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item.get_content())
        return chapters

    def chapter_to_text(self, chapter):
        output = ''
        soup = BeautifulSoup(chapter, 'html.parser')
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            if output != "":
                output += "\n" + p.text
            else:
                output = p.text
        return output

    def html_to_text(self, thtml):
        Output = []
        for html in thtml:
            text = self.chapter_to_text(html)
            Output.append(text)
        return "\n".join(Output)

    def clean_latin1(self, data):
        LATIN_1_CHARS = (
            ('\xe2\x80\x99', "'"),
            ('\xc3\xa9', 'e'),
            ('\xe2\x80\x90', '-'),
            ('\xe2\x80\x91', '-'),
            ('\xe2\x80\x92', '-'),
            ('\xe2\x80\x93', '-'),
            ('\xe2\x80\x94', '-'),
            ('\xe2\x80\x94', '-'),
            ('\xe2\x80\x98', "'"),
            ('\xe2\x80\x9b', "'"),
            ('\xe2\x80\x9c', '"'),
            ('\xe2\x80\x9c', '"'),
            ('\xe2\x80\x9d', '"'),
            ('\xe2\x80\x9e', '"'),
            ('\xe2\x80\x9f', '"'),
            ('\xe2\x80\xa6', '...'),
            ('\xe2\x80\xb2', "'"),
            ('\xe2\x80\xb3', "'"),
            ('\xe2\x80\xb4', "'"),
            ('\xe2\x80\xb5', "'"),
            ('\xe2\x80\xb6', "'"),
            ('\xe2\x80\xb7', "'"),
            ('\xe2\x81\xba', "+"),
            ('\xe2\x81\xbb', "-"),
            ('\xe2\x81\xbc', "="),
            ('\xe2\x81\xbd', "("),
            ('\xe2\x81\xbe', ")")
        )

        for _hex, _char in LATIN_1_CHARS:
            data = data.replace(_hex, _char)
        return data


if __name__ == "__main__":
    extractor = TextExtractor()

    downloads = "data-mining/book-downloader/downloads"
    folders = os.listdir(downloads)

    for folder in folders:
        # if folder in ["fiction", "action"]:
        #     continue

        files = os.listdir(f"{downloads}/{folder}")
        print(folder)
        for file in files:
            filename, ext = os.path.splitext(file)

            try:
                if ext == ".epub":
                    chaps = extractor.epub_to_html(
                        f"{downloads}/{folder}/{file}")
                    strings = extractor.html_to_text(chaps)
                    text = extractor.clean_latin1(strings)

                if ext == ".pdf":
                    text = extractor.pdf_to_text(
                        f"{downloads}/{folder}/{file}")

                with open(f"data-mining/text-extraction/extracted/{filename}.txt", "w", encoding="utf-8") as textfile:
                    textfile.write(text)

                print("\t" + file)
            except Exception as error:
                print(F"\tFAILED : {filename}")

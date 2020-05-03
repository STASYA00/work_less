# work_less
Let's take advantage of task automation! Why to waste our time, when we have so little of it? There are a plenty of tools that allow us to free our time, and here are some of them.

## Springer Books Download
Springer is an amazing website that offers a range of books in open access. In this period, due to COVID-19, it offered 400 more books to be downloaded for free. However, not all of us can afford spending a couple of hours on downloading all these books. So I wrote a small script that can do all the job for you, getting all the books springer has in open access - and sorting them by categories. Moreover, you can have a catalog of these books with all the relevant information (local path, link, doi, author, title, category, keywords).

### Dependencies
* pandas
* urllib

### How To:

download zip file or:

```
git clone https://github.com/STASYA00/work_less.git

```
activate the virtual environment with the necessary dependencies.
run

```
python springer_books.py PATH PAGES

```

PATH - path to your Library directory (where all the books will be stored in the corresponding folders).
PAGES - number of pages to parse (make a preliminary check on the website)

### Result

As a result you will get a set of folders corresponding to the Springer-defined categories for the books, with the downloaded books inside. The script will automatically create a catalog.csv file for you, with the following information:

* Book title
* Book author
* DOI
* keywords
* Category
* Local Path
* Springer link
* Springer PDF link

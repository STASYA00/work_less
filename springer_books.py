import argparse
import os
import pandas as pd
import re
import urllib
from urllib.request import urlopen


class SpringerBooks:
	def __init__(self, bookpath, pages):
		"""
		Initializes the class.
		Input: bookpath       book library path, str

		"""
		assert isinstance(bookpath, str), 'Wrong format of the bookpath,'
		' expected type str, got {0}'.format(type(bookpath))

		assert isinstance(pages, int), 'Wrong format of the pages number,'
		' expected type int, got {0}'.format(type(pages))

		assert pages > 0, "Wrong input in the number of pages, " \
		                  "should be a positive integer."

		self.main_link = 'https://link.springer.com/'  # main website ref, str
		self.bookpath = bookpath  # path to the book library dir, str
		self._check_bookpath()
		self.pages = pages  # number of pages on springer, int
		self.links = []
		self.titles = []
		self.authors = {}
		self.topics = []
		self.kwrd = []
		self.df = pd.DataFrame()
		self.regex = dict(
			links=re.compile('/book/10.10[0-9]{2}/[0-9]*-?\d*-?\d*-?\d*-?\d'),
			titles=re.compile('title="[a-zA-Z0-9 ü,-—:;&–öä]*">(.*)</a>'),
			kwrd=re.compile("'kwrd': \[(.*)\]"),
			topics=re.compile('"primarySubject":"(\D*?)"'),
			authors=re.compile('"author-text">([a-zA-Z ]*?)<'),
			authors2=re.compile('"authors__name">(.*?)<'))

	def _check_bookpath(self):
		if self.bookpath[-1] != '/':
			self.bookpath = self.bookpath + '/'

	def _correct_title(self, _books):
		"""
		Eliminates the confusing symbols in the books' titles
		Input: _books          a list of book titles, list
		Output: _books         a list of corrected book titles, list

		"""
		for i, _title in enumerate(_books):
			for symbol in ['?', '!', ',', ':', ';', '&', '/', '.', "\t"]:
				if symbol in _title:
					_title = _title.replace(symbol, '')
			_books.insert(i, _title)
			_books = _books[: i + 1] + _books[i + 2:]
		return _books

	def _get_references(self, _which):
		"""
		Gets the compiled regex for the required data.
		Input: _which         key for the regex dictionary, can be:
							  'links'    - to get the links to pdfs
							  'titles'   - to get the book titles
							  'kwrd'     - to get the keywords for the book
							  'topics'   - to get the category the book belongs to
							  'authors'  - to get the authors of the book
							  'authors2' - in case the first author regex does not work
		Output: compiled regex
		"""
		assert _which in self.regex.keys(), "Unknown key for regex dictionary"
		return self.regex[_which]

	def _correct_authors(self):
		"""
		Corrects the imperfections in the authors' names (\xa0 symbol)

		"""
		for key, value in self.authors.items():
			new_value = []
			for name in list(value):
				new_value.append(name.replace('\xa0', ' '))
			self.authors[key] = new_value

	def _download_book(self, folder, book, link):
		"""
		Downloads the book from the website.
		Input: folder         name of the folder in the book library to sort the books, str
			   book           book title, str
			   link           DOI of the book (springer), str
		"""
		self._check_dir(folder)
		try:
			urllib.request.urlretrieve(
				'https://link.springer.com/content/pdf' + link[5:] + '.pdf',
				self.bookpath + folder + '/' + book + '.pdf')
		except Exception:
			print('Failed to load the book {0} into the folder {1}.'.format(book,
			                                                            folder))

	def _check_dir(self, _dir):
		dirs = os.listdir(self.bookpath)
		if _dir not in dirs:
			os.mkdir(self.bookpath + _dir)

	def get_books(self):
		for page in range(self.pages):
			html = urlopen(self.main_link + 'search/page/' +
			               str(page) +
			'?facet-content-type=%22Book%22&package=openaccess').read().decode(
			'utf-8')

			link_search = self._get_references('links').findall(html)
			titles_search = self._get_references('titles').findall(html)[2:]

			titles_search = self._correct_title(titles_search)

			# Check that all the books from the page have loaded correctly
			if len(link_search) < 20:
				if page != self.pages - 1:
					print(' did not load all the book links, control'
					      ' page {0} for the discrepancies in DOI'.format(page))

			for i, [link, title] in enumerate(zip(link_search, titles_search)):
				book_html = urlopen(self.main_link + link).read().decode(
					'utf-8')
				try:
					self.kwrd.append(
						self._get_references('kwrd').findall(
							book_html)[0])  # Keywords
				except IndexError:
					self.kwrd.append(0)

				_author_set = self._get_references('authors').findall(book_html)
				if not set(_author_set):
					# Sometimes authors are referenced differently
					_author_set = self._get_references('authors2').findall(
						book_html)

				# dictionary with authors' names
				self.authors[i] = set(_author_set)
				# topic to sort the books into folders
				self.topics.append(self._get_references(
					'topics').findall(book_html)[0])
				self._download_book(self.topics[-1], title, link)

			self.links = self.links + link_search
			self.titles = self.titles + titles_search

		self._correct_authors()

	def create_catalog(self, name='catalog'):
		"""
		Creates a catalog of the downloaded books in the bookpath dir.
		Input: name     name of the .csv file, default 'catalog.csv'

		"""
		assert isinstance(name, str), "Wrong format of the filename." \
		                              "Expected str, got {0}.".format(type(name))

		titles = pd.Series(data=self.titles, name='Title')
		theme = pd.Series(data=self.topics, name='Topic')
		keywords = pd.Series(data=self.kwrd, name='Keywords')
		bookauthor = pd.Series(data=self.authors, name='Authors')
		doi = pd.Series(data=[link[6:] for link in self.links], name='DOI')
		spr_link = pd.Series(data=[self.main_link + link for link in self.links],
		                     name='Springer_links')
		spr_pdf = pd.Series(
			data=[self.main_link + 'content/pdf' + link[5:] + '.pdf' for link in
			      self.links], name='Springer_pdf')
		self.df = pd.concat(
			[titles, theme, keywords, bookauthor, doi, spr_link, spr_pdf],
			axis=1)
		self.df['Local_Path'] = self.df.apply(
			lambda row: self.bookpath + row['Topic'] + '/' + row['Title'],
			axis=1)

		self.df.to_csv(self.bookpath + name + '.csv')


if __name__ == "__main__":
	s = SpringerBooks('D:/Temporary/books/', 2)
	s.get_books()
	s.create_catalog()

import argparse
import os
import pandas as pd
import re
import textwrap
import urllib
from urllib.request import urlopen

################################################################################

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=textwrap.dedent('''\
        USAGE: python springer_books.py /books [51] [-C] [-v]
        
        Levels of verbosity:
        
        -v      details, printing the downloaded component
        -vv     some operational details
        
        ------------------------------------------------------------------------
        
        This script downloads the books from Springer webiste in free access and
        categorizes them based on the topics. In the end of the script's 
        execution you will have a set of folders corresponding to the books'
        topics with the .pdf files inside. If you want to have a catalog of the
        downloaded books pass -D option. There is also an option that allows you
        to check whether there are new books in free access on the website and 
        download the missing ones: -C path_to_catalog.csv. File should have the
        links to the downloaded books in the column named 'Springer_links'.
        
        ------------------------------------------------------------------------
        
        '''))
parser.add_argument('path', type=str, help='path to save the books to, str',
                    default='')

parser.add_argument('--pages', '-p', type=int, help='number of pages to parse, '
                                                    'int. If no parameter passed'
                                                    ' will parse all the pages.')
parser.add_argument('--check', '-C', default='', type=str,
					 help='Option that only checks and downloads the files ' \
					      'available on springer and missing in your catalog.' \
					      'Pass your catalog as a path to the .csv file. Book ' \
					      'links should be in the column called Springer_links')
parser.add_argument('--verbose', '-v', action='count', default=0,
	                    help='If active, prints out the debug messages. For '
                             'more detailed messages use -vv or -vvv')
parser.add_argument('--database', '-D', action='store_true',
					 help='Option that makes a catalog.csv file in the '
					      'provided library directory.')

args = parser.parse_args()

################################################################################

PATH = args.path

CHECK = args.check

VERBOSE = args.verbose

if args.pages:
	PAGES = args.pages
else:
	PAGES = 0

################################################################################

# TODO: make an option to download books only from selected category[ies]
# TODO: option to choose the nargs of pages
# TODO: language option


class SpringerBooks:
	def __init__(self, bookpath, pages=0, v=0):
		"""
		Initializes the class.
		Input: bookpath       book library path, str

		"""
		assert isinstance(bookpath, str), 'Wrong format of the bookpath,'
		' expected type str, got {0}'.format(type(bookpath))

		assert isinstance(pages, int), 'Wrong format of the pages number,'
		' expected type int, got {0}'.format(type(pages))

		assert pages >= 0, "Wrong input in the number of pages, " \
		                   "should be a positive integer."

		self.VERBOSE = v

		self.main_link = 'https://link.springer.com/'  # main website ref, str
		self.bookpath = bookpath  # path to the book library dir, str
		self._check_bookpath()
		self.pages = pages  # number of pages on springer, int
		if self.pages == 0:
			self.get_pages_number()
		self.links = []
		self.titles = []
		self.authors = []  # change to dict later -?
		self.topics = []
		self.kwrd = []
		self.df = pd.DataFrame()
		self.regex = dict(
			links=re.compile('/book/10.10[0-9]{2}/[0-9]*-?\d*-?\d*-?\d*-?\d'),
			# titles=re.compile('title="[a-zA-Z0-9 ü,-—:;&–öä]*">(.*)</a>'),
			titles=re.compile('<title>([a-zA-Z0-9 ü,-—:;&–öä\'\’]*) \| SpringerLink<'),
			kwrd=re.compile("'kwrd': \[(.*)\]"),
			topics=re.compile('"primarySubject":"(\D*?)"'),
			# authors=re.compile('"author-text">([a-zA-Z ]*?)<'),
			authors=re.compile('"authors__name">(.*?)<'))

	def print_debug(self, _phrase, _verbosity):
		"""
		Prints out messages for debugging if VERBOSE is set to TRUE
		:param _phrase: str or a printable type, message to display
		:param _verbosity: int, level of verbosity, defines which messages to
		display (detail level)
		:return:
		"""
		if 0 < _verbosity <= self.VERBOSE:
			print(str(_phrase))

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

	def _check_dir(self, _dir):
		"""
		Checks whether the topic directory exists in your library.
		If it doesn't a new directory is created.
		:param _dir: name of the directory (topic), str
		:return:
		"""
		dirs = os.listdir(self.bookpath)
		if _dir not in dirs:
			os.mkdir(self.bookpath + _dir)

	def	_correct_authors(self):
		"""
		Corrects the imperfections in the authors' names (\xa0 symbol)

		"""
		for i, _author in enumerate(self.authors):
			new_value = []
			for name in list(author):
				new_value.append(name.replace('\xa0', ' '))
			self.authors[i] = new_value

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
			print('Failed to load the book'
			      ' {0} into the folder {1}.'.format(book, folder))

	def get_pages_number(self):
		_html = urlopen('https://link.springer.com/search/page/1?facet-content'
		                '-type=%22Book%22&package=openaccess').read().decode(
							'utf-8')
		pages_regex = re.compile('name=\"total-pages\" value=\"(\d*)"\/')
		test_str = 'typropoesdkj name="total-pages" value="10"/>'
		self.print_debug(
			'Trial info is {0}'.format(pages_regex.findall(test_str)[0]), 1)
		self.print_debug('Page info is {0}'.format(pages_regex.findall(_html)[0]), 1)
		self.pages = int(pages_regex.findall(_html)[0])


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

	def _get_links(self):
		_check_links = []
		for page in range(self.pages):
			html = urlopen(self.main_link + 'search/page/' +
			               str(page) +
			               '?facet-content-type=%22Book%22&package=openaccess').read().decode(
							'utf-8')
			link_search = self._get_references('links').findall(html)
			if len(link_search) < 20:
				if page != self.pages - 1:
					print(' did not load all the book links, control'
					      ' page {0} for the discrepancies in DOI'.format(page))
			_check_links = _check_links + link_search
		return _check_links

	def _get_info(self, _html, _which):
		html = urlopen(_html).read().decode('utf-8')
		search = self._get_references(_which).findall(html)
		if _which == 'titles':
			# search = search[2:]
			search = self._correct_title(search)[0]
		elif _which == 'kwrd':
			search = search
		elif _which == 'author':
			search = set(search)[0]
		else:
			search = search[0]
		self.print_debug(search, 2)
		return search

	def get_books(self):
		for page in range(self.pages):
			html = urlopen(self.main_link + 'search/page/' +
			               str(page) +
			'?facet-content-type=%22Book%22&package=openaccess').read().decode(
			'utf-8')

			link_search = self._get_references('links').findall(html)
			# titles_search = self._get_references('titles').findall(html)[2:]
			# titles_search = self._correct_title(titles_search)

			# Check that all the books from the page have loaded correctly
			if len(link_search) < 20:
				if page != self.pages - 1:
					print(' did not load all the book links, control'
					      ' page {0} for the discrepancies in DOI'.format(page))

			for i, link in enumerate(link_search):
				print(self.main_link + link)
				book_html = self.main_link[:-1] + link
				self.titles.append(self._get_info(book_html, 'titles'))
				self.authors.append(self._get_info(book_html, 'authors'))
				self.topics.append(self._get_info(book_html, 'topics'))
				try:
					self.kwrd.append(self._get_info(book_html,
					                                'kwrd'))  # Keywords
				except IndexError:
					self.kwrd.append(0)
				self._download_book(self.topics[-1],
				                    self._get_info(book_html, 'titles'), link)

			self.links = self.links + link_search
		self._correct_authors()

	###########################
	# Catalog functions.

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
		self.print_debug('Your catalog file has been successfully written.', 1)

	def check_catalog(self, csv='internal'):
		"""
		Checks the entries in catalog and compares it with the existing springer
		books in open access. Writes a new catalog file that contains the new
		entries as well.
		:param csv: path to the catalog file containing the links to the
		existing books, str
		:return: prints the missing books
		"""
		assert isinstance(csv, str)
		if csv != 'internal':
			self.df = pd.read_csv(csv, index_col=0)
		assert 'Springer_links' in self.df.columns, 'Cannot find the ' \
		                                            'Springer_links column in ' \
		                                            'your csv file'
		if len(self.links) == 0:
			self.links = self._get_links()
		_l = [self.main_link[:-1] + link for link in self.links]
		for _link in list(set(_l) - set(self.df['Springer_links'])):
			self._download_book(self._get_info(_link, 'topics'),
			                    self._get_info(_link, 'titles'),
			                    _link[len(self.main_link[:-1]):])

			_comment = 'Book {0} by {1} has been downloaded into {2}'
			self.print_debug(_comment.format(self._get_info(_link, 'titles'),
			                                 self._get_info(_link, 'authors'),
			                                 self._get_info(_link, 'topics')),
			                 1)

			self.df = self.df.append({'Title': self._get_info(_link, 'titles'),
			                          'Topic': self._get_info(_link, 'topics'),
			                          'Keywords': self._get_info(_link, 'kwrd'),
			                          'Author': self._get_info(_link,
			                                                   'authors'),
			                          'DOI': _link[
			                                 len(self.main_link[:-1]) + 6:],
			                          'Springer_links': _link,
			                          'Springer_pdfs': 'https://link.springer'
			                                           '.com/content/pdf' +
			                                           _link[len(self.main_link[
			                                                     :-1]) + 5:] +
			                                           '.pdf',
			                          'Local_Path': self.bookpath +
			                                        self._get_info(_link,
			                                                       'topics') +
			                                        '/' + self._get_info(_link,
			                                                             'titles') +
			                                        '.pdf'}, ignore_index=True)
		self.df.to_csv(self.bookpath + 'catalog.csv')
		self.print_debug('Your catalog file has been successfully updated.', 1)


if __name__ == "__main__":
	s = SpringerBooks(PATH, PAGES, v=VERBOSE)
	if len(CHECK) == 0:
		s.get_books()
	if args.database:
		s.create_catalog()
	if len(CHECK) > 0:
		print(s.check_catalog(csv=CHECK))

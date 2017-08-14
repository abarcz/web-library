#!/usr/bin/python
# -*- coding: UTF-8 -*-
# vim: set fileencoding=utf-8 :

"""
Copyright 2017 Aleksy Barcz

This file is part of WebLibrary.

WebLibrary is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

WebLibrary is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with WebLibrary; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

"""
ModPythonPublisher server
"""

from mako.template import Template
from library import *
from config import *

class Entry():
	title = ""
	author = ""
	available = ""
	borrower = ""
	due_date = ""
	overdue = ""
	holder = ""


def build_entries(library):
	books = library.books.values()
	entries = []
	for book in books:
		entry = Entry()
		entry.title = book.title
		entry.author = book.author
		entry.available = library.available(book.title)
		if not entry.available:
			entry.borrower = library.checked_by(book.title)
			entry.due_date = library.due_date(book.title)
			entry.overdue = library.is_overdue(book.title)
		if library.is_held(book.title):
			entry.holder = library.held_by(book.title)
		entries.append(entry)
	return entries

def index(req, borrower=None, holder=None, borrowed_title=None, returned_title=None, unheld_title=None):
	persistence = PersistenceManager(DB_PATH)
	persistence.connect()
	library = persistence.load()
	if borrower != None:
		library.check_out(borrowed_title, borrower)
		persistence.store(library)
	elif holder != None:
		library.hold(borrowed_title, holder)
		persistence.store(library)
	elif returned_title != None:
		library.bring_back(returned_title)
		persistence.store(library)
	elif unheld_title != None:
		library.remove_hold(unheld_title)
		persistence.store(library)
	entries = build_entries(library)
	persistence.close()
	template = Template(filename=PATH + "library.mako", format_exceptions=True)
	return template.render(title=PAGE_TITLE, books=entries, users=library.users.keys())

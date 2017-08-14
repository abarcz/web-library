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
Backend for managing a simple library:
+ adding books
+ checking out books and returning them

Additional:
+ making reservations on checked-out books
- sending notification email when books are due (TODO)

To run unit tests, run in scripts directory:
$ py.test
"""

from datetime import date, timedelta

import sqlalchemy
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Date, Boolean
from sqlalchemy import and_

Base = declarative_base()

class User(Base):
	__tablename__ = "users"
	username = Column(String, primary_key=True)

	def __init__(self, username):
		self.username = username


class Book(Base):
	__tablename__ = "books"
	title = Column(String, primary_key=True)
	author = Column(String)

	def __init__(self, title, author):
		self.title = title
		self.author = author


class Hold(Base):
	__tablename__ = "holds"
	username = Column(String, ForeignKey("users.username"), primary_key=True)
	title = Column(String, ForeignKey("books.title"), primary_key=True)
	_user = relationship(User, backref=backref("_holds", cascade="all, delete-orphan"))
	_book = relationship(Book, backref=backref("_holds", cascade="all, delete-orphan"))

	def __init__(self, title, username):
		self.title = title
		self.username = username


class CheckOut(Base):
	__tablename__ = "checkouts"
	user = Column(String, ForeignKey("users.username"), primary_key=True)
	title = Column(String, ForeignKey("books.title"), primary_key=True)
	checked = Column(Date, primary_key=True)
	due_date = Column(Date)
	returned = Column(Boolean)
	_user = relationship(User, backref=backref("_checkouts", cascade="all, delete-orphan"))
	_book = relationship(Book, backref=backref("_checkouts", cascade="all, delete-orphan"))

	def __init__(self, title, user, checked, due_date):
		self.title = title
		self.user = user
		self.checked = checked
		self.due_date = due_date
		self.returned = False

	def same(self, other):
		if isinstance(other, self.__class__):
			return self.title == other.title and self.user == other.user and self.checked == other.checked
		return NotImplemented


class Library():

	def __init__(self, books = [], usernames = []):
		self.checked_out = {}
		self.books = {}
		self.users = {}
		self.holds = {}
		self.checkout_days = 30
		for book in books:
			self.add_book(book)
		for username in usernames:
			self.users[username] = User(username)

	def has_user(self, username):
		return username in self.users.keys()

	def add_book(self, book):
		self.books[book.title] = book

	def has_book(self, title):
		return title in self.books

	def available(self, title):
		return not title in self.checked_out.keys()

	def check_out(self, title, username):
		if not username in self.users.keys():
			raise Exception("Cannot check out book '%s' for non-existent user '%s'" % (title, username))
		if not self.available(title):
			raise Exception("Cannot check out book '%s' : not available" % title)
		checked = date.today()
		due_date = checked + timedelta(days=self.checkout_days)
		self.checked_out[title] = CheckOut(title, username, checked, due_date)
		if self.held_by(title) == username:
			self.remove_hold(title)

	def remove_hold(self, title):
		assert(title in self.holds.keys())
		self.holds.pop(title)

	def bring_back(self, title):
		if not title in self.checked_out.keys():
			raise Exception("Book not checked out: '%s' cannot be returned" % title)
		self.checked_out.pop(title)

	def checked_by(self, title):
		if not title in self.checked_out.keys():
			return None
		return self.checked_out[title].user

	def checked_date(self, title):
		if not title in self.checked_out.keys():
			return None
		return self.checked_out[title].checked

	def due_date(self, title):
		if not title in self.checked_out.keys():
			return None
		return self.checked_out[title].due_date

	def is_overdue(self, title):
		if not title in self.checked_out.keys():
			return None
		return self.due_date(title) <= date.today()

	def held_by(self, title):
		if not title in self.holds.keys():
			return None
		return self.holds[title]

	def is_held(self, title):
		return self.held_by(title) != None

	def hold(self, title, username):
		if self.available(title):
			raise Exception("Cannot hold book '%s' which is available" % title)
		if self.held_by(title) != None:
			raise Exception("Cannot hold book '%s' which is held" % title)
		if self.checked_by(title) == username:
			raise Exception("Cannot hold book '%s', because user is the same as borrower" % title)
		self.holds[title] = username


class PersistenceManager():
	def __init__(self, db_path):
		self.engine = sqlalchemy.create_engine(db_path)

	def create_tables(self):
		Base.metadata.create_all(self.engine)

	def connect(self):
		self.Session = sessionmaker(bind=self.engine)
		self.session = self.Session()

	def close(self):
		self.session.rollback()	# rollback uncommited changes
		self.session.close()
		self.session.bind.dispose()	# session.close() doesn't close the session

	def store(self, library):
		items = self._collect_items(library)
		self.session.query(Hold).delete()	# nonoptimal but it's sufficient
		self.session.add_all(items)
		self.session.commit()

	def _collect_items(self, library):
		items = []
		items.extend(self._get_new_books(library))
		items.extend(self._get_new_users(library))
		returned_checkouts = self._mark_returned_checkouts(library)
		items.extend(returned_checkouts)
		new_checkouts = self._get_new_checkouts(library)
		items.extend(new_checkouts)
		items.extend(self._get_holds(library))
		return items

	def _get_new_books(self, library):
		db_books = self.session.query(Book).all()
		new_books = []
		for title, book in library.books.items():
			found = False
			for db_book in db_books:
				if title == db_book.title:
					found = True
					break
			if not found:
				new_books.append(book)
		return new_books

	def _get_new_users(self, library):
		db_users = self.session.query(User).all()
		new_users = []
		for username, user in library.users.items():
			found = False
			for db_user in db_users:
				if username == db_user.username:
					found = True
					break
			if not found:
				new_users.append(user)
		return new_users

	def _mark_returned_checkouts(self, library):
		db_checkouts = self.session.query(CheckOut).all()
		returned_checkouts = []
		for db_checkout in db_checkouts:
			if db_checkout.returned:
				continue
			found = False
			for checkout in library.checked_out.values():
				if db_checkout.same(checkout):
					found = True
					break
			if not found:
				db_checkout.returned = True
				returned_checkouts.append(db_checkout)
		return returned_checkouts

	def _get_new_checkouts(self, library):
		db_checkouts = self.session.query(CheckOut).all()
		new_checkouts = []
		for checkout in library.checked_out.values():
			found = False
			for db_checkout in db_checkouts:
				if db_checkout.same(checkout):
					if db_checkout.returned:
						assert(not checkout.returned)
						db_checkout.returned = False
						new_checkouts.append(db_checkout)
					found = True
					break
			if not found:
				new_checkouts.append(checkout)
		return new_checkouts

	def _get_holds(self, library):
		holds = []
		for title, username in library.holds.items():
			holds.append(Hold(title, username))
		return holds

	def load(self):
		library = Library()
		books = self.session.query(Book).all()
		for book in books:
			library.add_book(book)
		users = self.session.query(User).all()
		for user in users:
			library.users[user.username] = user
		checkouts = self._load_pending_checkouts()
		for checkout in checkouts:
			assert(library.has_book(checkout.title))
			assert(library.available(checkout.title))
			library.checked_out[checkout.title] = checkout
		holds = self.session.query(Hold).all()
		for hold in holds:
			library.holds[hold.title] = hold.username
		return library

	def _load_pending_checkouts(self):
		checkouts = self.session.query(CheckOut).all()
		pending_checkouts = []
		for checkout in checkouts:
			if not checkout.returned:
				pending_checkouts.append(checkout)
		return pending_checkouts

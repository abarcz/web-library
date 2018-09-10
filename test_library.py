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

from library import *
import pytest
from datetime import date, timedelta

@pytest.fixture()
def book():
	return Book("Clean Code", "R.C. Martin")

@pytest.fixture()
def book2():
	return Book("Clean Architecture", "R.C. Martin")

@pytest.fixture()
def user1():
	return User("AB", "ab@ab.pl")

@pytest.fixture()
def user2():
	return User("CD", "cd@cd.com")

@pytest.fixture()
def library(book, book2, user1, user2):
	library = Library([book, book2], [user1, user2])
	library.check_out("Clean Architecture", "AB")
	return library

@pytest.fixture()
def persistence():
	#persistence = PersistenceManager("postgresql://postgres:postgres@localhost:5432/library")
	persistence = PersistenceManager("sqlite:///:memory:")
	persistence.create_tables()
	return persistence

def test_user_email(user1):
	assert(user1.email == "ab@ab.pl")

def test_user_exists(library):
	assert(library.has_user("AB"))

def test_no_user(library):
	assert(not library.has_user("AG"))

def test_create_book(book):
	assert(book.title == "Clean Code")
	assert(book.author == "R.C. Martin")

def test_book_exists(library):
	assert(library.has_book("Clean Code"))

def test_book_exists2(library):
	assert(library.has_book("Clean Architecture"))

def test_book_not_exists(library):
	assert(not library.has_book("Dirty Code"))

def test_book_available(library):
	assert(library.available("Clean Code"))

def test_no_user_for_checkout(library):
	with pytest.raises(Exception):
		library.check_out("Clean Code", "AG")

def test_book_checked_out(library):
	assert(not library.available("Clean Architecture"))

def test_no_check_out_if_checked_out(library):
	with pytest.raises(Exception):
		library.check_out("Clean Architecture", "AB")

def test_book_checked_by(library):
	assert(library.checked_by("Clean Architecture") == "AB")

def test_book_checked_by2(library):
	assert(library.checked_by("Clean Code") is None)

def test_no_hold(library):
	assert(library.held_by("Clean Architecture") == None)
	assert(not library.is_held("Clean Architecture"))

def test_hold(library):
	library.hold("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == "CD")
	assert(library.is_held("Clean Architecture"))

def test_remove_hold(library):
	library.hold("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == "CD")
	assert(library.is_held("Clean Architecture"))
	library.remove_hold("Clean Architecture")
	assert(not library.is_held("Clean Architecture"))

def test_checkout_removes_hold(library):
	library.hold("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == "CD")
	assert(library.checked_by("Clean Architecture") == "AB")
	library.bring_back("Clean Architecture")
	assert(library.held_by("Clean Architecture") == "CD")
	library.check_out("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == None)
	assert(library.checked_by("Clean Architecture") == "CD")

def test_cannot_hold_if_borrower(library):
	with pytest.raises(Exception):
		library.hold("Clean Architecture", "AB")

def test_double_hold(library):
	library.hold("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == "CD")
	library.hold("Clean Architecture", "CD")
	assert(library.held_by("Clean Architecture") == "CD")

def test_different_hold(library):
	library.hold("Clean Architecture", "CD")
	with pytest.raises(Exception):
		library.hold("Clean Architecture", "AB")
	assert(library.held_by("Clean Architecture") == "CD")

def test_no_hold_available(library):
	assert(library.held_by("Clean Code") == None)

def test_cannot_hold_available(library):
	with pytest.raises(Exception):
		library.hold("Clean Code", "CD")
	assert(library.held_by("Clean Code") == None)

def test_book_returned(library):
	library.bring_back("Clean Architecture")
	assert(library.available("Clean Architecture"))
	assert(library.due_date("Clean Architecture") is None)

def test_cannot_return(library):
	with pytest.raises(Exception):
		library.bring_back("Dirty Code")

def test_not_due(library):
	assert(library.due_date("Clean Code") is None)

def test_due(library):
	assert(library.due_date("Clean Architecture") == date.today() + timedelta(days=library.checkout_days))

def test_not_overdue(library):
	assert(not library.is_overdue("Clean Architecture"))

def test_overdue(library):
	library.checkout_days = 0
	library.check_out("Clean Code", "AB")
	assert(library.is_overdue("Clean Code"))

def test_not_checked(library):
	assert(library.checked_date("Clean Code") is None)

def test_checked(library):
	assert(library.checked_date("Clean Architecture") == date.today())

def test_persistence(library, persistence):
	persistence.connect()
	library.hold("Clean Architecture", "CD")
	persistence.store(library)
	library2 = persistence.load()
	assert(library2.checked_by("Clean Architecture") == "AB")
	assert(library2.due_date("Clean Architecture") == date.today() + timedelta(days=library.checkout_days))
	assert(not library2.available("Clean Architecture"))
	assert(library2.held_by("Clean Architecture") == "CD")
	assert(library2.available("Clean Code"))
	assert(library2.has_book("Clean Code"))
	persistence.close()

def test_double_store(library, persistence):
	persistence.connect()
	persistence.store(library)
	persistence.store(library)
	library2 = persistence.load()
	assert(library2.checked_by("Clean Architecture") == "AB")
	assert(library2.due_date("Clean Architecture") == date.today() + timedelta(days=library.checkout_days))
	assert(not library2.available("Clean Architecture"))
	assert(library2.available("Clean Code"))
	assert(library2.has_book("Clean Code"))
	assert(library2.has_user("AB"))
	persistence.close()

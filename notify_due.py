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

from library import *
from config import *
import os

persistence = PersistenceManager(DB_PATH)
persistence.connect()
library = persistence.load()

for title in library.books.keys():
	if library.is_overdue(title):
		username = library.checked_by(title)
		email = library.get_user(username).email
		command = "echo -e \\\"Subject: " + OVERDUE_SUBJECT + "\n\n" + OVERDUE_TEXT % title + "\\\" | sendmail -F " + OVERDUE_SENDER + " -f " + OVERDUE_SENDER_EMAIL + " " + email
		os.system('GREPDB="%s"; /bin/bash -c "$GREPDB"' % command)

persistence.close()

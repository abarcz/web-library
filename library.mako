## -*- coding: utf-8 -*-

<!--
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
-->

<html>
<head>
	<meta charset="utf-8">
	<title>${title}</title>
</head>

<body lang="pl-PL">
	<div id="container">
		<div id="main">
			<table width="100%" border="1">
			<tbody>
				% for book in books:
					<%
						book_title = book.title
						author = book.author
						bg_color_due = "FFFFFF"
						borrower_input = "borrower"
						borrower_button = "Check out"
						book_users = list(users)
						disable_unhold = "disabled"
						return_button = "Return"
						unhold_button = "Unhold"
						if book.available:
							bg_color = "A0FFA0"
							due_text = "available"
							disable_checkout = ""
							disable_return = "disabled"
							if book.holder != "":
								book_users = [book.holder]
						else:
							disable_checkout = "disabled"
							disable_return = ""
							if book.overdue:
								bg_color_due = "FF0000"
							bg_color = "C0C0C0"
							book_users.remove(book.borrower)
							due_text = "borrowed by: %s, due: %s" % (book.borrower, book.due_date)
							return_button = return_button + " (%s)" % book.borrower
							if book.holder == "":
								disable_checkout = ""
								borrower_input = "holder"
								borrower_button = "Hold"
						if book.holder != "":
							due_text = due_text + " (next: %s)" % book.holder
							unhold_button = unhold_button + " (%s)" % book.holder
							disable_unhold = ""
					%>
					<tr>
						<td style="background-color: ${bg_color};">${book_title} (${author})</td>
						<td style="background-color: ${bg_color_due};">${due_text}</td>
						<td>
							<form action="index.py" method="get">
								<select name="${borrower_input}">
								% for user in book_users:
									<option value="${user}">${user}</option>
								% endfor
								</select>
								<button ${disable_checkout} type="submit">${borrower_button}</button>
								<input type="hidden" name="borrowed_title" value="${book_title}"/> 
							</form>
						</td>
						<td>
							<form action="index.py" method="get">
								<button ${disable_return} type="submit">${return_button}</button>
								<input type="hidden" name="returned_title" value="${book_title}"/> 
							</form>
						</td>
						<td>
							<form action="index.py" method="get">
								<button ${disable_unhold} type="submit">${unhold_button}</button>
								<input type="hidden" name="unheld_title" value="${book_title}"/> 
							</form>
						</td>
					</tr>
				% endfor
			</tbody>
			</table>
		</div><!-- main -->
	</div><!-- container -->
</body>
</html>

## vim:ft=mako

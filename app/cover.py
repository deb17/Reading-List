from operator import attrgetter

import openlibrary
from flask import flash

def get_isbn(title, author):

    if not author or not author.strip():   # just incase author is none
        list_a = []
    else:
        author = author.replace(' and ', ',')
        list_a = [name.strip() for name in author.split(',')]

    # search_value = title.replace(' ', '+')

    try:
        api = openlibrary.BookSearch()
        # res = api.get_by_title(search_value)
        res = api.get_by_title(title)
        isbn = process_results(res, list_a, title)
    except Exception:
        flash('Open Library access error. Cover cannot be shown.')
        return None

    if isbn:
        return isbn
    else:
        flash('Book not in Open Library. Cover cannot be shown.')
        return None

def process_results(res, list_a, title):

    docs = []
    for doc in res.docs[:10]:
        if (isinstance(doc.first_publish_year, int) and
                doc.lang in ('eng', None)):
            docs.append(doc)
    docs.sort(key=attrgetter('first_publish_year'), reverse=True)

    for doc in docs:
        if doc.title.lower() == title.lower():
            if doc.author and list_a:
                list_b = []
                if isinstance(doc.author, str):
                    list_b.append(doc.author)
                elif isinstance(doc.author, list):
                    list_b = doc.author

                for a in list_a:
                    if all(a not in name for name in list_b):
                        break
                else:
                    isbn = format_isbn(doc.isbn)
                    if isbn:
                        break
            elif list_a:
                continue
            else:
                isbn = format_isbn(doc.isbn)
                if isbn:
                    break
    else:
        isbn = ''

    return isbn

def format_isbn(doc_isbn):

    if isinstance(doc_isbn, list) and doc_isbn:
        isbn = doc_isbn[-1]
    elif isinstance(doc_isbn, str):
        isbn = doc_isbn
    else:
        isbn = ''
    return isbn

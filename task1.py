import tkinter as tk
from tkinter import messagebox, ttk
from pymongo import MongoClient
from datetime import datetime

class LibraryApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Library Manager - My Project")
        self.window.geometry("600x400")  # Smaller window for one page at a time

        # Connect to MongoDB
        try:
            self.mongo = MongoClient("mongodb://localhost:27017/")
            self.db = self.mongo["library"]
            self.books = self.db["books"]
            self.lending = self.db["lending_records"]
            print("Yay, MongoDB is connected!")
        except Exception as e:
            messagebox.showerror("Error", f"Couldn’t connect to MongoDB: {e}")
            return

        # Container for switching pages
        self.container = tk.Frame(self.window)
        self.container.pack(fill="both", expand=True)

        # dictionary to hold the pages
        self.pages = {}

        # Create the two pages (Books and Lending)
        for PageClass in (BooksPage, LendingPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # navigation buttons at the top
        self.nav_frame = tk.Frame(self.window)
        self.nav_frame.pack(fill="x", pady=5)
        tk.Button(self.nav_frame, text="Manage Books", command=lambda: self.show_page("BooksPage")).pack(side="left", padx=10)
        tk.Button(self.nav_frame, text="Lending System", command=lambda: self.show_page("LendingPage")).pack(side="left", padx=10)

        # show the books page by default
        self.show_page("BooksPage")

    def show_page(self, page_name):
        # bring the selected page to the front
        page = self.pages[page_name]
        page.tkraise()
        # refresh the data when switching pages
        if page_name == "BooksPage":
            page.show_books()
        else:
            page.show_lending()


# Page for managing books
class BooksPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # books section
        self.books_frame = tk.LabelFrame(self, text="Books Collection", padx=10, pady=10)
        self.books_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # labels and inputs for adding a book
        tk.Label(self.books_frame, text="Title:").grid(row=0, column=0, sticky="w")
        self.title_entry = tk.Entry(self.books_frame)
        self.title_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.books_frame, text="Author:").grid(row=1, column=0, sticky="w")
        self.author_entry = tk.Entry(self.books_frame)
        self.author_entry.grid(row=1, column=1, pady=5)

        tk.Label(self.books_frame, text="Genre:").grid(row=2, column=0, sticky="w")
        self.genre_entry = tk.Entry(self.books_frame)
        self.genre_entry.grid(row=2, column=1, pady=5)

        tk.Label(self.books_frame, text="Quantity:").grid(row=3, column=0, sticky="w")
        self.quantity_entry = tk.Entry(self.books_frame)
        self.quantity_entry.grid(row=3, column=1, pady=5)

        # bnuttons for adding, deleting, and lending
        tk.Button(self.books_frame, text="Add Book", command=self.add_book).grid(row=4, column=0, pady=5)
        tk.Button(self.books_frame, text="Delete Book", command=self.delete_book).grid(row=4, column=1, pady=5)
        tk.Button(self.books_frame, text="Lend Selected Book", command=self.lend_selected_book).grid(row=5, column=0, columnspan=2, pady=5)

        #  show books
        self.book_view = ttk.Treeview(self.books_frame, columns=("Title", "Author", "Genre", "Quantity"), show="headings")
        self.book_view.heading("Title", text="Title")
        self.book_view.heading("Author", text="Author")
        self.book_view.heading("Genre", text="Genre")
        self.book_view.heading("Quantity", text="Quantity")
        self.book_view.grid(row=6, column=0, columnspan=2, pady=5, sticky="nsew")
        self.show_books()

    def add_book(self):
        # gain the input values
        title = self.title_entry.get()
        author = self.author_entry.get()
        genre = self.genre_entry.get()
        quantity = self.quantity_entry.get()

        # see if everything is filled
        if not title or not author or not genre or not quantity:
            messagebox.showwarning("Missing Info", "Please fill in all the fields!")
            return

        # Make sure quantity is a valid number
        try:
            quantity = int(quantity)
            if quantity <= 0:
                messagebox.showerror("Invalid Quantity", "Quantity must be a positive number!")
                return
        except ValueError:
            messagebox.showerror("Invalid Quantity", "Quantity must be a number!")
            return

        # adds the book to the database
        book = {"title": title, "author": author, "genre": genre, "quantity": quantity}
        self.controller.books.insert_one(book)
        messagebox.showinfo("Success", "Book added to the library!")
        self.show_books()
        self.clear_book_fields()

    def show_books(self):
        # clear the current view and show all books
        for item in self.book_view.get_children():
            self.book_view.delete(item)
        for book in self.controller.books.find():
            self.book_view.insert("", "end", values=(book["title"], book["author"], book["genre"], book["quantity"]))

    def delete_book(self):
        # delete a selected book
        selected = self.book_view.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a book to delete!")
            return

        title = self.book_view.item(selected)["values"][0]
        self.controller.books.delete_one({"title": title})
        messagebox.showinfo("Success", "Book deleted from the library!")
        self.show_books()

    def lend_selected_book(self):
        # switch to the lending page and pre-fill the book title
        selected = self.book_view.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a book to lend!")
            return

        book_title = self.book_view.item(selected)["values"][0]
        self.controller.show_page("LendingPage")
        lending_page = self.controller.pages["LendingPage"]
        lending_page.lend_book_entry.delete(0, tk.END)
        lending_page.lend_book_entry.insert(0, book_title)

    def clear_book_fields(self):
        # clear book input fields
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.genre_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)


# Page for managing lending
class LendingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # lending section
        self.lending_frame = tk.LabelFrame(self, text="Lending System", padx=10, pady=10)
        self.lending_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # inputs for lending a book
        tk.Label(self.lending_frame, text="Book Title:").grid(row=0, column=0, sticky="w")
        self.lend_book_entry = tk.Entry(self.lending_frame)
        self.lend_book_entry.grid(row=0, column=1, pady=5)

        tk.Label(self.lending_frame, text="Borrower Name:").grid(row=1, column=0, sticky="w")
        self.borrower_entry = tk.Entry(self.lending_frame)
        self.borrower_entry.grid(row=1, column=1, pady=5)

        tk.Label(self.lending_frame, text="Borrow Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w")
        self.borrow_date_entry = tk.Entry(self.lending_frame)
        self.borrow_date_entry.grid(row=2, column=1, pady=5)

        tk.Label(self.lending_frame, text="Return Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="w")
        self.return_date_entry = tk.Entry(self.lending_frame)
        self.return_date_entry.grid(row=3, column=1, pady=5)

        # lending actions
        tk.Button(self.lending_frame, text="Lend Book", command=self.lend_book).grid(row=4, column=0, pady=5)
        tk.Button(self.lending_frame, text="Return Book", command=self.return_book).grid(row=4, column=1, pady=5)
        tk.Button(self.lending_frame, text="Update Return Date", command=self.update_return).grid(row=5, column=0, pady=5)
        tk.Button(self.lending_frame, text="Delete Lending Record", command=self.delete_lending).grid(row=5, column=1, pady=5)

        # show lending records
        self.lending_view = ttk.Treeview(self.lending_frame, columns=("Book Title", "Borrower", "Borrow Date", "Return Date"), show="headings")
        self.lending_view.heading("Book Title", text="Book Title")
        self.lending_view.heading("Borrower", text="Borrower")
        self.lending_view.heading("Borrow Date", text="Borrow Date")
        self.lending_view.heading("Return Date", text="Return Date")
        self.lending_view.grid(row=6, column=0, columnspan=2, pady=5, sticky="nsew")
        self.show_lending()

    def lend_book(self):
        # Get lending details
        book_title = self.lend_book_entry.get()
        borrower = self.borrower_entry.get()
        borrow_date = self.borrow_date_entry.get()
        return_date = self.return_date_entry.get()

        # Check if all fields are filled
        if not book_title or not borrower or not borrow_date or not return_date:
            messagebox.showwarning("Missing Info", "Please fill in all lending details!")
            return

        # Validate the dates
        try:
            datetime.strptime(borrow_date, "%Y-%m-%d")
            datetime.strptime(return_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Dates must be in YYYY-MM-DD format!")
            return

        # Check if the book exists and has copies available
        book = self.controller.books.find_one({"title": book_title})
        if not book:
            messagebox.showerror("Book Not Found", "That book isn’t in the library!")
            return
        if book["quantity"] <= 0:
            messagebox.showerror("Out of Stock", "No copies available to lend!")
            return

        # update quantity and add lending record
        self.controller.books.update_one({"title": book_title}, {"$inc": {"quantity": -1}})
        lending_record = {
            "book_title": book_title,
            "borrower_name": borrower,
            "borrow_date": borrow_date,
            "return_date": return_date
        }
        self.controller.lending.insert_one(lending_record)
        messagebox.showinfo("Success", "Book has been lent out!")
        self.show_lending()
        self.clear_lending_fields()

    def show_lending(self):
        # clear and show all lending records
        for item in self.lending_view.get_children():
            self.lending_view.delete(item)
        for record in self.controller.lending.find():
            self.lending_view.insert("", "end", values=(record["book_title"], record["borrower_name"], record["borrow_date"], record["return_date"]))

    def update_return(self):
        # update the return date for a lending record
        selected = self.lending_view.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a lending record!")
            return

        new_return_date = self.return_date_entry.get()
        if not new_return_date:
            messagebox.showwarning("Missing Info", "Please enter a new return date!")
            return

        try:
            datetime.strptime(new_return_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Return date must be in YYYY-MM-DD format!")
            return

        book_title = self.lending_view.item(selected)["values"][0]
        borrower = self.lending_view.item(selected)["values"][1]
        self.controller.lending.update_one(
            {"book_title": book_title, "borrower_name": borrower},
            {"$set": {"return_date": new_return_date}}
        )
        messagebox.showinfo("Success", "Return date updated!")
        self.show_lending()

    def return_book(self):
        # ret a book by deleting the lending record and restoring quantity
        selected = self.lending_view.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a lending record to return!")
            return

        book_title = self.lending_view.item(selected)["values"][0]
        borrower = self.lending_view.item(selected)["values"][1]
        self.controller.lending.delete_one({"book_title": book_title, "borrower_name": borrower})
        self.controller.books.update_one({"title": book_title}, {"$inc": {"quantity": 1}})
        messagebox.showinfo("Success", "Book returned to the library!")
        self.show_lending()

    def delete_lending(self):
        # dlete a lending record without returning the book 
        selected = self.lending_view.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a lending record to delete!")
            return

        book_title = self.lending_view.item(selected)["values"][0]
        borrower = self.lending_view.item(selected)["values"][1]
        self.controller.lending.delete_one({"book_title": book_title, "borrower_name": borrower})
        messagebox.showinfo("Success", "Lending record deleted!")
        self.show_lending()

    def clear_lending_fields(self):
        # clear lending input fields
        self.lend_book_entry.delete(0, tk.END)
        self.borrower_entry.delete(0, tk.END)
        self.borrow_date_entry.delete(0, tk.END)
        self.return_date_entry.delete(0, tk.END)


#rns app
if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
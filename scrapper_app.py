import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import requests
import json
import os
import re
import multiprocessing
from customtkinter import CTkImage
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from e_commerce_scraper.spiders.jumia_spider import JumiaSpiderSpider
from e_commerce_scraper.spiders.amazon_spider import AmazonSpiderSpider


def run_spiders_in_process(product_name):
    settings = get_project_settings()
    runner = CrawlerRunner(settings=settings)
    runner.crawl(JumiaSpiderSpider, product_name=product_name)
    runner.crawl(AmazonSpiderSpider, product_name=product_name)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())
    reactor.run(installSignalHandlers=0)

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("E-Commerce Scraper")
        self.root.state('zoomed')

        # Set the app window size to match the monitor size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.resizable(width=False, height=False)

        # Set CustomTkinter theme
        ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("dark-blue")  # Options: "blue", "green"

        # Product Name Input
        self.label = ctk.CTkLabel(root, text="Enter Product Name:")
        self.label.pack(pady=10)

        self.product_entry = ctk.CTkEntry(root, width=400)
        self.product_entry.pack(pady=10)

        # Scrape Button
        self.scrape_button = ctk.CTkButton(root, text="Scrape", command=self.start_scraping)
        self.scrape_button.pack(pady=10)

        # Filter Options
        self.filter_frame = ctk.CTkFrame(root)
        self.filter_frame.pack(pady=10)

        self.filter_label = ctk.CTkLabel(self.filter_frame, text="Filter by:")
        self.filter_label.grid(row=0, column=0, padx=5)

        self.filter_options = ctk.CTkComboBox(self.filter_frame, values=["Price (Low to High)", "Price (High to Low)", "Rating (High to Low)"])
        self.filter_options.grid(row=0, column=1, padx=5)
        self.filter_options.set("Price (Low to High)")

        self.filter_button = ctk.CTkButton(self.filter_frame, text="Apply Filter", command=self.apply_filter)
        self.filter_button.grid(row=0, column=2, padx=5)

        # TabView for Product Details
        self.tabview = ctk.CTkTabview(root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Add the first tab for all products
        self.all_products_tab = self.tabview.add("All Products")
        self.setup_all_products_tab()

        # Store scraped data
        self.scraped_data = []
        self.scraping_process = None

    def setup_all_products_tab(self):
        # Scrollable Frame for Results
        self.canvas = ctk.CTkCanvas(self.all_products_tab, width=self.root.winfo_screenwidth() - 100, height=self.root.winfo_screenheight() - 200, bg=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1])
        self.scrollbar = ctk.CTkScrollbar(self.all_products_tab, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)

        # Configure the scrollable frame to expand
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def start_scraping(self):
        if os.path.exists("scraped_data.json"):
            os.remove("scraped_data.json")
        product_name = self.product_entry.get().strip()
        if not product_name:
            messagebox.showwarning("Input Error", "Please enter a product name.")
            return

        # Disable UI elements
        self.scrape_button.configure(state="disabled")
        self.filter_button.configure(state="disabled")
        self.product_entry.configure(state="disabled")
        self.filter_options.configure(state="disabled")

        self.clear_results()
        self.results_text = ctk.CTkLabel(self.scrollable_frame, text="Scraping in progress... Please wait.", font=("Arial", 14))
        self.results_text.pack(pady=20)

        # Run the Scrapy spiders in a separate process
        self.run_spiders(product_name)

    def run_spiders(self, product_name):
        # Use multiprocessing to run the spiders in a separate process
        self.scraping_process = multiprocessing.Process(
            target=run_spiders_in_process,
            args=(product_name,)
        )
        self.scraping_process.start()
        # Start checking the process status
        self.root.after(100, self.check_scraping_process)

    def check_scraping_process(self):
        if self.scraping_process.is_alive():
            # Check again after 100ms
            self.root.after(100, self.check_scraping_process)
        else:
            # Re-enable UI elements
            self.scrape_button.configure(state="normal")
            self.filter_button.configure(state="normal")
            self.product_entry.configure(state="normal")
            self.filter_options.configure(state="normal")

            # Process finished, display results
            self.display_results()
            self.scraping_process = None

    def extract_price(self, price):
        """Extract and convert price to a float, handling lists and strings."""
        if isinstance(price, list):
            price = price[0] if price else "0"
        price = re.sub(r"[^\d.]", "", str(price))  # Remove non-numeric characters
        return float(price) if price else 0.0

    def display_results(self):
        results_file = os.path.abspath("scraped_data.json")

        if not os.path.exists(results_file):
            self.results_text.configure(text="No data found. Scraping may have failed.")
            return

        try:
            self.scraped_data = []  # Initialize an empty list to store the parsed JSON objects
            with open(results_file, "r", encoding='utf-8') as file:
                for line in file:
                    try:
                        # Parse each line as a JSON object and append it to the list
                        self.scraped_data.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        print(f"Skipping invalid JSON line: {line.strip()}")

            if not self.scraped_data:
                self.results_text.configure(text="No valid data found in the JSON file.")
                return

            self.results_text.destroy()  # Clear the progress message
            self.apply_filter()  # Display results with the default filter

        except Exception as e:
            if hasattr(self, "results_text"):
                self.results_text.configure(text=f"Error: {str(e)}")

    def apply_filter(self):
        # Clear existing results
        self.clear_results()

        # Get the selected filter
        filter_option = self.filter_options.get()

        try:
            # Sort the scraped data based on the selected filter
            if filter_option == "Price (Low to High)":
                sorted_data = sorted(self.scraped_data, key=lambda x: self.extract_price(x.get("product_price", "0")))
            elif filter_option == "Price (High to Low)":
                sorted_data = sorted(self.scraped_data, key=lambda x: self.extract_price(x.get("product_price", "0")),
                                     reverse=True)
            elif filter_option == "Rating (High to Low)":
                sorted_data = sorted(self.scraped_data, key=lambda x: float(x.get("product_rate", "0"))
                                     if x.get("product_rate", "0").replace('.', '', 1).isdigit() else 0, reverse=True)
            else:
                sorted_data = self.scraped_data

            # Display the sorted results in 4 columns
            num_columns = 3
            for index, product in enumerate(sorted_data):
                row = index // num_columns
                col = index % num_columns
                self.display_product(product, row, col)
        except Exception as e:
            print(f"Error applying filter: {e}")

    def display_product(self, product, row, col):
        # Set a wider frame width (e.g., 350)
        frame_width = 350  # Adjust this value as needed
        frame = ctk.CTkFrame(self.scrollable_frame, border_width=2, corner_radius=10, width=frame_width)
        frame.grid(row=row, column=col, padx=20, pady=10, sticky="nsew")  # Adjust padding if needed

        # Bind click event to the frame
        frame.bind("<Button-1>", lambda e, p=product: self.show_product_details(p))

        # Load and display image (keep size reasonable)
        img_label = ctk.CTkLabel(frame, text="")
        img_label.grid(row=0, column=0, rowspan=5, padx=10, pady=10)
        self.load_image(product.get("img_url", ""), img_label)

        # Bind click event to the image label
        img_label.bind("<Button-1>", lambda e, p=product: self.show_product_details(p))

        # Display product details in a structured format
        details = [
            ("Title", self.clean_text(product.get("product_title", ""))),
            ("Price", self.clean_text(product.get("product_price", ""))),
            ("Brand", self.clean_text(product.get("brand", ""))),
            ("Rating", self.clean_text(product.get("product_rate", ""))),
            ("Reviews", self.clean_text(product.get("number_of_rates", ""))),
            ("Website", "Amazon" if self.clean_text(product.get("product_url", "")).count("amazon") != 0 else "Jumia")
        ]

        for i, (label, value) in enumerate(details):
            label_label = ctk.CTkLabel(frame, text=f"{label}:", font=("Arial", 12, "bold"))
            label_label.grid(row=i, column=1, sticky="w", padx=5, pady=2)

            value_label = ctk.CTkLabel(frame, text=value, wraplength=250, justify="left")  # Increase wraplength
            value_label.grid(row=i, column=2, sticky="w", padx=5, pady=2)

            # Bind click event to labels
            label_label.bind("<Button-1>", lambda e, p=product: self.show_product_details(p))
            value_label.bind("<Button-1>", lambda e, p=product: self.show_product_details(p))

    def show_product_details(self, product):
        # Create a new tab for the product
        tab_name = self.clean_text(product.get("product_title"))
        if tab_name in self.tabview._tab_dict:
            # If the tab already exists, switch to it
            self.tabview.set(tab_name)
        else:
            # Add a new tab
            tab = self.tabview.add(tab_name)
            self.display_product_in_tab(tab, product)
            self.add_close_button_to_tab(tab_name)

    def display_product_in_tab(self, tab, product):
        # Create a scrollable frame for the tab
        scrollable_frame = ctk.CTkScrollableFrame(tab, width=800, height=600)  # Adjust width and height as needed
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create a main frame for organizing layout
        main_frame = ctk.CTkFrame(scrollable_frame)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Display image in a larger format
        img_frame = ctk.CTkFrame(main_frame, corner_radius=10, border_width=2)
        img_frame.pack(side="left", padx=10, pady=10, fill="y")

        img_label = ctk.CTkLabel(img_frame, text="", width=300, height=300)  # Adjust width and height for image
        img_label.pack(pady=10)
        self.load_image(product.get("img_url", ""), img_label, (280, 280))

        # Button to view product on website
        if product.get("product_url"):
            url_button = ctk.CTkButton(img_frame, text="View Product on Website", fg_color="green",
                                       hover_color="darkgreen", command=lambda: self.open_url(product["product_url"]))
            url_button.pack(pady=20)

        # Close button for the tab
        close_button = ctk.CTkButton(img_frame, text="Close Tab", fg_color="red", hover_color="darkred",
                                     command=lambda: self.close_tab(self.tabview.get()))
        close_button.pack(pady=10)

        # Display product details in another column
        details_frame = ctk.CTkFrame(main_frame, corner_radius=10, border_width=2)
        details_frame.pack(side="right", padx=10, pady=10, fill="both", expand=True)

        details = [
            ("Title", self.clean_text(product.get("product_title", "")), ("Arial", 16, "bold")),
            ("Price", self.clean_text(product.get("product_price", "")), ("Arial", 14, "bold")),
            ("Brand", self.clean_text(product.get("brand", "")), ("Arial", 14)),
            ("Rating",
             f"⭐ {self.clean_text(product.get('product_rate', ''))} ({self.clean_text(product.get('number_of_rates', ''))} reviews)",
             ("Arial", 14)),
            ("Description", self.clean_text(product.get("description", "")), ("Arial", 12)),
            ("Features", "\n".join(product.get("features", [])), ("Arial", 12)),
            ("Details", "\n".join([f"{key}: {value}" for key, value in product.get("details", {}).items()]),
             ("Arial", 12)),
            ("Colors", self.clean_text(product.get("colors", "")), ("Arial", 12)),
        ]

        for label, value, font in details:
            # Create a frame for each detail
            detail_frame = ctk.CTkFrame(details_frame, corner_radius=10, border_width=2)
            detail_frame.pack(fill="x", padx=10, pady=5)

            # Add label (bold and larger font)
            label_label = ctk.CTkLabel(detail_frame, text=f"{label}:", font=font)
            label_label.pack(side="left", padx=10, pady=5)

            # Add value (normal font)
            value_label = ctk.CTkLabel(detail_frame, text=value, wraplength=600, justify="left", font=("Arial", 12))
            value_label.pack(side="left", padx=10, pady=5)

        # Display reviews if available
        reviews = product.get("reviews", {})
        if isinstance(reviews, dict):  # Check if reviews is a dictionary
            reviews_frame = ctk.CTkFrame(details_frame, corner_radius=10, border_width=2)
            reviews_frame.pack(fill="x", padx=10, pady=10)

            reviews_label = ctk.CTkLabel(reviews_frame, text="Customer Reviews", font=("Arial", 14, "bold"))
            reviews_label.pack(pady=10)

            for review_key, review in reviews.items():
                review_frame = ctk.CTkFrame(reviews_frame, corner_radius=10, border_width=1)
                review_frame.pack(fill="x", padx=10, pady=5)
                rating_float = float(review.get("review_rate", 0))
                rating = int(rating_float)
                stars = "⭐" * rating
                rating_label = ctk.CTkLabel(review_frame, text=f"Rating: {stars}", font=("Arial", 12, "bold"))
                rating_label.pack(anchor="w", padx=10, pady=5)

                review_text = review.get("review_text", "")
                review_text_label = ctk.CTkLabel(review_frame, text=review_text, wraplength=600, justify="left",
                                                 font=("Arial", 12))
                review_text_label.pack(anchor="w", padx=10, pady=5)

                author = review.get("reviewer_name", "")
                date = review.get("review_date", "")
                verified = review.get("verified_purchase", "")
                author_date_label = ctk.CTkLabel(review_frame, text=f"By {author} on {date} ({verified})",
                                                 font=("Arial", 10), fg_color="gray")
                author_date_label.pack(anchor="w", padx=10, pady=5)
        else:
            # Handle the case where reviews is not a dictionary (e.g., a string)
            reviews_frame = ctk.CTkFrame(details_frame, corner_radius=10, border_width=2)
            reviews_frame.pack(fill="x", padx=10, pady=10)

            reviews_label = ctk.CTkLabel(reviews_frame, text="Customer Reviews", font=("Arial", 14, "bold"))
            reviews_label.pack(pady=10)

            no_reviews_label = ctk.CTkLabel(reviews_frame, text=reviews, font=("Arial", 12))
            no_reviews_label.pack(pady=10)


    def add_close_button_to_tab(self, tab_name):
        # Add a close button to the tab
        tab = self.tabview._tab_dict[tab_name]
        close_button = ctk.CTkButton(tab, text="X", width=20, height=20, command=lambda: self.close_tab(tab_name))
        close_button.pack(side="right", padx=5, pady=5)

    def close_tab(self, tab_name):
        # Close the specified tab
        if tab_name != "All Products":  # Prevent closing the first tab
            self.tabview.delete(tab_name)

    def load_image(self, img_url, img_label, size=(90, 90)):
        try:
            # Download the image from the URL
            response = requests.get(img_url, stream=True)
            response.raise_for_status()

            # Open the image using PIL
            img = Image.open(response.raw)

            # Resize the image if a size is provided
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)

            # Convert the PIL image to a CTkImage
            ctk_image = CTkImage(img, size=size if size else img.size)

            # Set the image in the label
            img_label.configure(image=ctk_image)
            img_label.image = ctk_image  # Keep a reference to avoid garbage collection

        except Exception as e:
            print(f"Error loading image: {e}")
            img_label.configure(text="Image not available")

    def clean_text(self, text):
        """Clean text by removing HTML tags, excessive whitespace, and special characters."""
        if isinstance(text, list):
            text = ", ".join(map(str, text))
        elif not isinstance(text, str):
            text = str(text)
        text = re.sub(r"<.*?>", "", text)  # Remove HTML tags
        text = re.sub(r"[\r\n\t]+", " ", text)  # Replace newlines and tabs with spaces
        text = re.sub(r"\s{2,}", " ", text)  # Replace multiple spaces with a single space
        return text.strip()

    def open_url(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open URL: {e}")

    def clear_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = ctk.CTk()
    app = ScraperApp(root)
    root.mainloop()

#Imports
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import csv
import time


#Initialize SQLite db
engine = create_engine("sqlite:///inventory.db", echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

def menu():
    choice = menu_prompt()
    if choice == 'V':
        view_details()
    elif choice == 'N':
        add_product()
    elif choice == 'A':
        analyze_db()
    elif choice == 'B':
        backup_db()


def menu_prompt():
    while True:
        print('''
                Programming Books
                \rV) View Details
                \rN) Add New Product
                \rA) Analysis
                \rB) Back Up Database''')
        
        choice = input('What would you like to do?\n')
        if choice in ['V','N','A','B']:
            return choice
        else:
            print('Error with your choice. Please choose one of the options below.\n')


def analyze_db():
    most_expensive = session.query(Product).order_by(Product.product_price.desc()).first()
    print(f'Most expensive: {most_expensive.product_name}')
    least_expensive = session.query(Product).order_by(Product.product_price).first()
    print(f'Least expensive: {least_expensive.product_name}')
    brands = session.query(Brands).all()
    the_brand = None
    max_products = 0
    for brand in brands:
        if len(brand.products) > max_products:
            max_products = len(brand.products)
            the_brand = brand
    print(f"{the_brand.brand_name} has the most products with: ({max_products} products)")


def add_product():
    while True:
        product_name = input('Product Name: ').strip()
        if len(product_name) > 0:
            break
        else:
            print("Product name cannot be blank.")
    
    quantity_error = True
    while quantity_error:
        product_quantity = input('Product Quantity: ')
        try:
            product_quantity = int(product_quantity)
            quantity_error = False
        except ValueError:
            print("Invalid quantity. Please enter a number (e.g., 12).")

    date_error = True
    while date_error:
        date_str = input('Date (EX: 11/1/2018): ')
        try:
            date = datetime.datetime.strptime(date_str, "%m/%d/%Y").date()
            date_error = False
        except ValueError:
            print("Invalid date format. Please use MM/DD/YYYY (e.g., 11/1/2018).")

    price_error = True
    while price_error:
        price = input('Price (Ex:25.04)')
        price = clean_price(price)
        if type(price) == int:
            price_error = False
            
    new_product = Product(product_name=product_name, product_quantity=product_quantity, date_updated=date, product_price=price)
    session.add(new_product)
    session.commit()
    print('Product Added Successfully')
    time.sleep(1.5)

def view_details():
    print("\nEnter the id of the product you want to view.")
    id_options = []
    for product in session.query(Product):
        id_options.append(product.product_id)
    if not id_options: 
        print("Database is empty.")
        return
    id_error = True
    while id_error:
        id_choice = input(f'''
            \rId Options: {id_options}
            \rProduct ID: ''')
        id_choice = clean_id(id_choice, id_options)
        if type(id_choice) == int:
            id_error = False
    the_product = session.query(Product).filter(Product.product_id==id_choice).first()
    print(f'\n{the_product.product_name} \nQuantity: {the_product.product_quantity} \nDate Updated: {the_product.date_updated}\nPrice: ${the_product.product_price / 100}')

def backup_db():
    with open("backup_inventory.csv", "w", newline="")as csvfile:
        writer = csv.writer(csvfile)
        field_names = ["product_name", "product_price", "product_quantity", "date_updated", "brand_name"]
        writer.writerow(field_names)
        products = session.query(Product).all()
        for product in products:
            price = f"${product.product_price / 100:.2f}"
            if product.brand:
                brand_name = product.brand.brand_name
            else:
                brand_name = "No Brand"
            writer.writerow([
                product.product_name,
                price,
                product.product_quantity,
                product.date_updated.strftime("%m/%d/%Y"),
                brand_name
            ])

    with open("backup_brands.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        field_names = ["brand_id", "brand_name"]
        writer.writerow(field_names)
        brands = session.query(Brands).all()
        for brand in brands:
            writer.writerow([brand.brand_id, brand.brand_name])

    print("Backed up databases to 'backup_brands.csv' and 'backup_inventory.csv'.")
    time.sleep(1.5)


def clean_id(id_str, options):
    try:
        product_id = int(id_str)
    except ValueError:
        input('''
        \n*****ID Error*****
              \rThe ID should be a number
              \rPress Enter to Try again.''')
        return
    else:
        if product_id in options:
            return product_id
        else:
            input(f'''
            \nID ERROR
            \rOptions: {options}
            \rPress enter to try again.
''')
            return

def clean_price(price_str):
    try:
        clean_str = price_str.replace("$", "").strip()
        price_float = float(clean_str)
    except ValueError:
        print(f"\n*****Price Error*****\nInvalid price: '{price_str}'")
        return None
    else:
        return int(price_float * 100)


def add_brands_csv():
    with open('brands.csv') as csvfile:
        data = csv.reader(csvfile)
        next(data)
        for row in data:
            brand_in_db = session.query(Brands).filter(Brands.brand_name == row[0]).one_or_none()

            if brand_in_db == None:
                brand_name = row[0]
                
                new_brand = Brands(brand_name=brand_name)
                session.add(new_brand)
        session.commit()

def add_inventory_csv():
    # product_id = Column(Integer, primary_key=True)
    # product_name = Column( String)
    # product_quantity = Column(Integer)
    # product_price = Column(Integer)
    # date_updated = Column(Date)
    with open('inventory.csv') as csvfile:
        data = csv.reader(csvfile)
        next(data)
        for row in data:
            inventory_in_db = session.query(Product).filter(Product.product_name == row[0]).one_or_none()
            if inventory_in_db == None:
                product_name = row[0]
                product_price = clean_price(row[1])
                product_quantity = int(row[2])
                date_updated = datetime.datetime.strptime(row[3], "%m/%d/%Y").date()
                brand_name = row[4]
                brand = session.query(Brands).filter(Brands.brand_name == brand_name).one_or_none()
                if brand is None:
                    print(f"Warning: Brand '{brand_name}' not found in database. Skipping product '{product_name}'.")
                    continue
                brand_id = brand.brand_id
                new_product = Product(
                    product_name=product_name,
                    product_price=product_price,
                    product_quantity=product_quantity,
                    date_updated=date_updated,
                    brand_id=brand_id
                )

                session.add(new_product)
        session.commit()


class Brands(Base):
    __tablename__ = "brands"

    brand_id = Column(Integer, primary_key=True)
    brand_name = Column(String)
    products = relationship("Product", back_populates="brand")

    

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True)
    product_name = Column( String)
    product_quantity = Column(Integer)
    product_price = Column(Integer)
    date_updated = Column(Date)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))
    brand = relationship("Brands", back_populates="products")
    
if __name__ == "__main__":
    Base.metadata.create_all(engine)

    add_brands_csv()
    add_inventory_csv()
    menu()
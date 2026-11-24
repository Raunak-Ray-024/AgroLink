
import json

from fastapi import FastAPI, HTTPException
from dtos import ProductDTO, OrderRequestDTO

FILE_NAME = "data.json"


# ---------------- DATA MANAGEMENT ----------------

def load_products():
    with open(FILE_NAME, "r") as file:
        return json.load(file)


def save_products(products):
    with open(FILE_NAME, "w") as file:
        json.dump(products, file, indent=4)


products = load_products()

app = FastAPI(title="Bharat AgroLink Marketplace")


# ---------------- HOME ----------------

@app.get("/home")
def home():
    return {"message": "Welcome to Bharat AgroLink"}


# ---------------- PRODUCT LISTING ----------------

@app.get("/products")
def get_products(category: str = None):

    if category:
        filtered_products = [
            p for p in products
            if p.get("category", "").lower() == category.lower()
        ]
        return filtered_products

    return products


# ---------------- SELLER PRODUCTS ----------------

@app.get("/seller/{seller_id}")
def get_seller(seller_id: int):

    seller_products = [
        p for p in products
        if p.get("seller_id") == seller_id
    ]

    if not seller_products:
        raise HTTPException(
            status_code=404,
            detail="Seller products not found"
        )

    return seller_products


# ---------------- CREATE PRODUCT ----------------

@app.post("/create_prod")
def create_product(prod_data: ProductDTO):

    new_prod = prod_data.model_dump()

    # Prevent duplicate seller-product combinations
    for p in products:
        if (
            p["seller_id"] == new_prod["seller_id"]
            and p["product"].lower() == new_prod["product"].lower()
        ):
            raise HTTPException(
                status_code=400,
                detail="Product already exists for this seller"
            )

    products.append(new_prod)

    save_products(products)

    return {
        "status": "success",
        "product": new_prod
    }


# ---------------- UPDATE PRODUCT ----------------

@app.put("/update_prod/{seller_id}/{product_name}")
def update_prod(
    seller_id: int,
    product_name: str,
    prod_data: ProductDTO
):

    for idx, oneProduct in enumerate(products):

        if (
            oneProduct["seller_id"] == seller_id
            and oneProduct["product"].lower() == product_name.lower()
        ):

            updated_data = prod_data.model_dump()

            products[idx] = updated_data

            save_products(products)

            return {
                "status": "success",
                "product": updated_data
            }

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )


# ---------------- ORDER SUMMARY ----------------

@app.post("/order_summary")
def order_summary(order: OrderRequestDTO):

    seller_orders = {}
    total_subtotal = 0

    for item in order.items:

        product = next(
            (
                p for p in products
                if p["seller_id"] == item.seller_id
                and p["product"].lower() == item.product.lower()
            ),
            None
        )

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"{item.product} not found for seller {item.seller_id}"
            )

        if item.quantity > product["stock"]:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product['product']}"
            )

        seller_id = product["seller_id"]

        subtotal = product["price"] * item.quantity

        if seller_id not in seller_orders:

            seller_orders[seller_id] = {
                "seller_id": seller_id,
                "seller": product.get("seller"),
                "products": [],
                "subtotal": 0
            }

        seller_orders[seller_id]["products"].append({
            "product": product["product"],
            "price": product["price"],
            "quantity": item.quantity,
            "total": subtotal
        })

        seller_orders[seller_id]["subtotal"] += subtotal

        total_subtotal += subtotal

    gst = round(total_subtotal * 0.18, 2)

    final_total = round(total_subtotal + gst, 2)

    return {
        "status": "success",
        "seller_wise_orders": list(seller_orders.values()),
        "order_summary": {
            "subtotal": total_subtotal,
            "gst_percentage": 18,
            "gst_amount": gst,
            "final_order_total": final_total
        }
    }

from pydantic import BaseModel, Field

class ProductDTO(BaseModel):
    seller_id: int
    product: str
    price: int = 0
    stock: int = 0
    category: str = "Other"


class OrderItemDTO(BaseModel):
    seller_id: int
    product: str
    quantity: int = Field(gt=0)


class OrderRequestDTO(BaseModel):
    items: list[OrderItemDTO]
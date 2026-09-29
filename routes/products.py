"""Rutas de la API de productos (CRUD completo)."""

from flask import Blueprint, jsonify, request

import services.product_service as service

products_bp = Blueprint("products_api", __name__, url_prefix="/api/products")


@products_bp.get("")
@products_bp.get("/")
def list_products():
    """GET /api/products?search=&category=&stock=low|out|available"""
    return jsonify(
        {
            "success": True,
            "count": len(
                service.list_products(
                    search=request.args.get("search"),
                    category=request.args.get("category"),
                    stock_filter=request.args.get("stock"),
                    order=request.args.get("order", "recent"),
                )
            ),
            "categories": service.CATEGORIES,
            "counts_by_category": service.counts_by_category(),
            "products": service.list_products(
                search=request.args.get("search"),
                category=request.args.get("category"),
                stock_filter=request.args.get("stock"),
                order=request.args.get("order", "recent"),
            ),
        }
    )


@products_bp.post("")
@products_bp.post("/")
def create_product():
    """POST /api/products"""
    data = request.get_json(silent=True) or request.form.to_dict()
    if "image" in request.files:
        data["image"] = service.save_image(request.files["image"])

    product = service.create_product(data)
    return jsonify({"success": True, "message": "Producto agregado correctamente.", "product": product}), 201


@products_bp.get("/<int:product_id>")
def get_product(product_id):
    """GET /api/products/<id>"""
    product = service.get_product(product_id)
    if product is None:
        return jsonify({"success": False, "message": "Producto no encontrado."}), 404
    return jsonify({"success": True, "product": product})


@products_bp.put("/<int:product_id>")
def update_product(product_id):
    """PUT /api/products/<id>"""
    data = request.get_json(silent=True) or request.form.to_dict()
    if "image" in request.files:
        data["image"] = service.save_image(request.files["image"])

    product = service.update_product(product_id, data)
    if product is None:
        return jsonify({"success": False, "message": "Producto no encontrado."}), 404
    return jsonify({"success": True, "message": "Producto actualizado correctamente.", "product": product})


@products_bp.delete("/<int:product_id>")
def delete_product(product_id):
    """DELETE /api/products/<id>"""
    service.delete_product(product_id)
    return jsonify({"success": True, "message": "Producto eliminado correctamente."})

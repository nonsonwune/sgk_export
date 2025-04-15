from app import create_app
from app.models.shipment import Shipment

app = create_app()
with app.app_context():
    shipments = Shipment.query.limit(5).all()
    for s in shipments:
        print(f"Shipment ID: {s.id}, Status: {s.status}") 
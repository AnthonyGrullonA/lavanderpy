from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import random


class Command(BaseCommand):
    help = "Carga datos de prueba completos con flujo de órdenes, inventario y caja."

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando seed de datos de prueba...")
        with transaction.atomic():
            self.create_units()
            self.create_inventory_items()
            self.create_service_catalog()
            self.create_customers()
            self.create_cash_register()
            self.create_orders()
        self.stdout.write(self.style.SUCCESS("✅ Seed completado correctamente."))

    # === 1️⃣ UNIDADES ===
    def create_units(self):
        from inventory.models import Unit

        units = ["ml", "unidad", "kg", "lt"]
        for u in units:
            Unit.objects.get_or_create(name=u, defaults={"abbreviation": u})
        self.stdout.write(f"🧩 Unidades creadas/verificadas: {', '.join(units)}")

    # === 2️⃣ INSUMOS ===
    def create_inventory_items(self):
        from inventory.models import InventoryItem, Unit

        ml = Unit.objects.filter(name="ml").first()
        unidad = Unit.objects.filter(name="unidad").first()

        items = [
            {"name": "Detergente líquido", "unit": ml, "current_stock": Decimal("5000.00"), "min_stock": Decimal("1000.00"), "cost_per_unit": Decimal("0.08")},
            {"name": "Suavizante", "unit": ml, "current_stock": Decimal("3000.00"), "min_stock": Decimal("500.00"), "cost_per_unit": Decimal("0.06")},
            {"name": "Bolsas de entrega", "unit": unidad, "current_stock": Decimal("200"), "min_stock": Decimal("50"), "cost_per_unit": Decimal("3.50")},
            {"name": "Blanqueador", "unit": ml, "current_stock": Decimal("2500.00"), "min_stock": Decimal("500.00"), "cost_per_unit": Decimal("0.05")},
        ]

        for it in items:
            InventoryItem.objects.update_or_create(
                name=it["name"],
                defaults={
                    "unit": it["unit"],
                    "current_stock": it["current_stock"],
                    "min_stock": it["min_stock"],
                    "cost_per_unit": it["cost_per_unit"],
                    "is_active": True,
                },
            )
        self.stdout.write(f"📦 Insumos cargados: {len(items)}")

    # === 3️⃣ SERVICIOS Y COMPONENTES ===
    def create_service_catalog(self):
        from catalog.models import ServiceCategory, Service, ServiceComponent
        from inventory.models import InventoryItem

        categories = [
            {"name": "Lavado", "description": "Lavado tradicional y por kilos"},
            {"name": "Planchado", "description": "Planchado y terminado"},
            {"name": "Tintorería", "description": "Limpieza en seco y especializada"},
        ]
        for c in categories:
            ServiceCategory.objects.update_or_create(name=c["name"], defaults={"description": c["description"]})

        services = [
            {"name": "Lavado por prenda", "category": "Lavado", "unit_type": "prenda", "base_price": Decimal("60.00")},
            {"name": "Lavado por kilo", "category": "Lavado", "unit_type": "kilo", "base_price": Decimal("90.00")},
            {"name": "Planchado sencillo", "category": "Planchado", "unit_type": "prenda", "base_price": Decimal("30.00")},
            {"name": "Tintorería camisa", "category": "Tintorería", "unit_type": "servicio", "base_price": Decimal("150.00")},
        ]

        for s in services:
            category = ServiceCategory.objects.get(name=s["category"])
            service, _ = Service.objects.update_or_create(
                name=s["name"],
                defaults={
                    "category": category,
                    "unit_type": s["unit_type"],
                    "base_price": s["base_price"],
                    "description": f"Servicio de {s['category'].lower()} automático.",
                    "is_active": True,
                },
            )

            # Vincular componentes
            detergent = InventoryItem.objects.filter(name__icontains="Detergente").first()
            suavizante = InventoryItem.objects.filter(name__icontains="Suavizante").first()
            bolsas = InventoryItem.objects.filter(name__icontains="Bolsas").first()
            blanqueador = InventoryItem.objects.filter(name__icontains="Blanqueador").first()

            if detergent:
                ServiceComponent.objects.update_or_create(service=service, item=detergent, defaults={"quantity_used": Decimal("50.0")})
            if "Lavado" in s["category"] and suavizante:
                ServiceComponent.objects.update_or_create(service=service, item=suavizante, defaults={"quantity_used": Decimal("15.0")})
            if "Planchado" in s["category"] and bolsas:
                ServiceComponent.objects.update_or_create(service=service, item=bolsas, defaults={"quantity_used": Decimal("1.0")})
            if "Tintorería" in s["category"] and blanqueador:
                ServiceComponent.objects.update_or_create(service=service, item=blanqueador, defaults={"quantity_used": Decimal("80.0")})

        self.stdout.write(f"🧺 Servicios y componentes creados: {len(services)}")

    # === 4️⃣ CLIENTES ===
    def create_customers(self):
        from customers.models import Customer

        clients = [
            {"name": "María Gómez", "customer_type": "personal", "email": "maria@example.com", "phone": "+1 809-111-0001", "address": "Calle 1", "contact_person": "", "credit_limit": 0},
            {"name": "Lavanderías Unidas SRL", "customer_type": "empresa", "email": "ventas@lu-srl.com", "phone": "+1 809-222-0002", "address": "Avenida Central 123", "contact_person": "Juan Pérez", "credit_limit": 10000},
            {"name": "Carlos Pérez", "customer_type": "personal", "email": "carlos@example.com", "phone": "+1 809-333-0003", "address": "Sector Los Jardines", "contact_person": "", "credit_limit": 0},
            {"name": "Hotel Colonial", "customer_type": "empresa", "email": "compras@hotelcolonial.com", "phone": "+1 809-444-0004", "address": "Zona Colonial", "contact_person": "Ana López", "credit_limit": 15000},
        ]

        for c in clients:
            Customer.objects.update_or_create(
                name=c["name"],
                defaults={
                    "customer_type": c["customer_type"],
                    "email": c["email"],
                    "phone": c["phone"],
                    "address": c["address"],
                    "contact_person": c["contact_person"],
                    "credit_limit": c["credit_limit"],
                    "is_active": True,
                },
            )
        self.stdout.write(f"👥 Clientes creados: {len(clients)}")

    # === 5️⃣ CAJA ===
    def create_cash_register(self):
        from cash.models import CashRegister
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()

        if not user:
            user = User.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")

        register, created = CashRegister.objects.get_or_create(
            name="Caja Principal",
            defaults={
                "opened_by": user,
                "opening_balance": Decimal("1000.00"),
                "is_open": True,
            },
        )

        status = "abierta" if register.is_open else "cerrada"
        self.stdout.write(f"💵 Caja principal {status}.")

    # === 6️⃣ ÓRDENES ===
    def create_orders(self):
        from orders.models import Order, OrderLine, OrderTracking
        from customers.models import Customer
        from catalog.models import Service
        from cash.models import CashRegister, CashMovement

        customers = list(Customer.objects.all())
        services = list(Service.objects.all())
        register = CashRegister.objects.filter(is_open=True).last()

        if not customers or not services:
            self.stdout.write(self.style.WARNING("⚠️ No hay clientes o servicios disponibles."))
            return

        orders_created = 0

        for i in range(12):
            customer = random.choice(customers)
            status = random.choice(["pendiente", "en_proceso", "listo", "entregado"])
            order = Order.objects.create(
                customer=customer,
                status=status,
                notes=f"Orden de prueba {i+1} ({status})",
                date_created=timezone.now() - timezone.timedelta(days=random.randint(0, 7)),
                discount=random.choice([0, 10, 25, 50]),
            )

            total = Decimal("0.00")
            for _ in range(random.randint(1, 3)):
                service = random.choice(services)
                qty = Decimal(random.randint(1, 5))
                unit_price = service.base_price
                subtotal = unit_price * qty
                OrderLine.objects.create(order=order, service=service, quantity=qty, unit_price=unit_price)
                total += subtotal

            order.total_amount = total
            order.final_amount = total - order.discount
            order.save(update_fields=["total_amount", "final_amount"])

            # 🔹 Si está en proceso o entregada, consumir inventario
            if status in ["en_proceso", "entregado"]:
                try:
                    order.consume_inventory()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error inventario: {e}"))

            # 🔹 Si está entregada → registrar movimiento de caja
            if status == "entregado" and register:
                from cash.models import CashMovement
                CashMovement.objects.create(
                    register=register,
                    movement_type="ingreso",
                    amount=order.final_amount,
                    description=f"Pago de orden {order.code}",
                    related_order=order,
                    created_by=register.opened_by,
                )

            OrderTracking.objects.create(
                order=order,
                previous_status=None,
                new_status=status,
                notes=f"Creación automática: {status}",
            )

            orders_created += 1

        self.stdout.write(f"🧾 Órdenes creadas: {orders_created}")

import pika
import json
import time


class Supplier:
    def __init__(self, supplier_name, equipment_types):
        self.supplier_name = supplier_name
        self.equipment_types = equipment_types

        self.admin_suppliers_queue = f"admin_suppliers_{supplier_name}"
        self.admin_all_queue = f"admin_all_supplier_{supplier_name}"

        print(f"[{self.supplier_name}] Zainicjalizowany: {', '.join(equipment_types)}")

    def start_listening(self):
        listen_connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        listen_channel = listen_connection.channel()

        for equipment_type in self.equipment_types:
            queue_name = f"orders_{equipment_type}"
            listen_channel.queue_declare(queue=queue_name)
            listen_channel.queue_bind(
                exchange="orders_exchange", queue=queue_name, routing_key=equipment_type
            )

        listen_channel.queue_declare(queue=self.admin_suppliers_queue)
        listen_channel.queue_bind(
            exchange="admin_to_suppliers", queue=self.admin_suppliers_queue
        )

        listen_channel.queue_declare(queue=self.admin_all_queue)
        listen_channel.queue_bind(
            exchange="admin_broadcast", queue=self.admin_all_queue
        )

        def callback_orders(ch, method, properties, body):
            order = json.loads(body)
            equipment_type = order["equipment_type"]

            print(
                f"[{self.supplier_name}] Otrzymano zlecenie "
                f"od {order['team_name']}: {equipment_type} (ID: {order['order_id']})"
            )

            # here the task would be processed

            confirmation = {
                "team_name": order["team_name"],
                "order_id": order["order_id"],
                "equipment_type": equipment_type,
                "supplier_name": self.supplier_name,
                "timestamp": time.time(),
            }

            listen_channel.basic_publish(
                exchange="confirmations_exchange",
                routing_key=order["team_name"],
                body=json.dumps(confirmation),
            )

            listen_channel.basic_publish(
                exchange="admin_copy",
                routing_key="",
                body=json.dumps({"type": "confirmation", "data": confirmation}),
            )

            print(
                f"[{self.supplier_name}] Wykonano zlecenie "
                f"od {order['team_name']}: {equipment_type} (ID: {order['order_id']})"
            )

        def callback_admin_suppliers(ch, method, properties, body):
            message = json.loads(body)
            print(
                f"[{self.supplier_name}] Wiadomość od Administratora (do Dostawców): {message['content']}"
            )

        def callback_admin_all(ch, method, properties, body):
            message = json.loads(body)
            print(
                f"[{self.supplier_name}] Wiadomość od Administratora (do wszystkich): {message['content']}"
            )

        for equipment_type in self.equipment_types:
            queue_name = f"orders_{equipment_type}"
            listen_channel.basic_consume(
                queue=queue_name, on_message_callback=callback_orders, auto_ack=True
            )

        listen_channel.basic_consume(
            queue=self.admin_suppliers_queue,
            on_message_callback=callback_admin_suppliers,
            auto_ack=True,
        )

        listen_channel.basic_consume(
            queue=self.admin_all_queue,
            on_message_callback=callback_admin_all,
            auto_ack=True,
        )

        print(f"[{self.supplier_name}] Nasłuchiwanie...")
        listen_channel.start_consuming()

    def close(self):
        pass  # closed on thread termination

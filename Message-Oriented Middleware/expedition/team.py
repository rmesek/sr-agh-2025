import pika
import json
import time


class Team:
    def __init__(self, team_name):
        self.team_name = team_name
        self.send_connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.send_channel = self.send_connection.channel()
        self.order_counter = 0

        self.confirmation_queue = f"confirmations_{team_name}"
        self.admin_teams_queue = f"admin_teams_{team_name}"
        self.admin_all_queue = f"admin_all_{team_name}"

        print(f"[{self.team_name}] Zainicjalizowany")

    def send_order(self, equipment_type):
        self.order_counter += 1
        order = {
            "team_name": self.team_name,
            "order_id": self.order_counter,
            "equipment_type": equipment_type,
            "timestamp": time.time(),
        }

        self.send_channel.basic_publish(
            exchange="orders_exchange",
            routing_key=equipment_type,
            body=json.dumps(order),
        )

        self.send_channel.basic_publish(
            exchange="admin_copy",
            routing_key="",
            body=json.dumps({"type": "order", "data": order}),
        )

        print(
            f"[{self.team_name}] Wysłano zlecenie: "
            f"{equipment_type} (ID: {self.order_counter})"
        )

    def start_listening(self):
        listen_connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        listen_channel = listen_connection.channel()

        listen_channel.queue_declare(queue=self.confirmation_queue)
        listen_channel.queue_bind(
            exchange="confirmations_exchange",
            queue=self.confirmation_queue,
            routing_key=self.team_name,
        )

        listen_channel.queue_declare(queue=self.admin_teams_queue)
        listen_channel.queue_bind(
            exchange="admin_to_teams", queue=self.admin_teams_queue
        )

        listen_channel.queue_declare(queue=self.admin_all_queue)
        listen_channel.queue_bind(
            exchange="admin_broadcast", queue=self.admin_all_queue
        )

        def callback_confirmations(ch, method, properties, body):
            confirmation = json.loads(body)
            print(
                f"[{self.team_name}] Otrzymano potwierdzenie od {confirmation['supplier_name']}: "
                f"{confirmation['equipment_type']} (ID: {confirmation['order_id']})"
            )

        def callback_admin_teams(ch, method, properties, body):
            message = json.loads(body)
            print(
                f"[{self.team_name}] Wiadomość od Administratora (do Ekip): {message['content']}"
            )

        def callback_admin_all(ch, method, properties, body):
            message = json.loads(body)
            print(
                f"[{self.team_name}] Wiadomość od Administratora (do wszystkich): {message['content']}"
            )

        listen_channel.basic_consume(
            queue=self.confirmation_queue,
            on_message_callback=callback_confirmations,
            auto_ack=True,
        )

        listen_channel.basic_consume(
            queue=self.admin_teams_queue,
            on_message_callback=callback_admin_teams,
            auto_ack=True,
        )

        listen_channel.basic_consume(
            queue=self.admin_all_queue,
            on_message_callback=callback_admin_all,
            auto_ack=True,
        )

        print(f"[{self.team_name}] Nasłuchiwanie...")
        listen_channel.start_consuming()

    def close(self):
        self.send_connection.close()

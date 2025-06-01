import pika
import json
import time


class Administrator:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost")
        )
        self.channel = self.connection.channel()

        self.copy_queue = "admin_copy_queue"
        self.channel.queue_declare(queue=self.copy_queue)
        self.channel.queue_bind(exchange="admin_copy", queue=self.copy_queue)

        print("[ADMINISTRATOR] Zainicjalizowany")

    def start_listening(self):
        def callback_listener(ch, method, properties, body):
            message = json.loads(body)
            msg_type = message["type"]
            data = message["data"]

            if msg_type == "order":
                print(
                    f"[ADMINISTRATOR] CC zlecenie: {data['team_name']} "
                    f"zamówiła: {data['equipment_type']} (ID: {data['order_id']})"
                )
            elif msg_type == "confirmation":
                print(
                    f"[ADMINISTRATOR] CC potwierdzenie: {data['supplier_name']} "
                    f"wykonał zlecenie dla {data['team_name']} (ID: {data['order_id']})"
                )

        self.channel.basic_consume(
            queue=self.copy_queue, on_message_callback=callback_listener, auto_ack=True
        )

        print("[ADMINISTRATOR] Nasłuchiwanie...")
        return self.channel

    def send_message_to_teams(self, content):
        message = {
            "content": content,
            "timestamp": time.time(),
            "from": "ADMINISTRATOR",
        }

        self.channel.basic_publish(
            exchange="admin_to_teams", routing_key="", body=json.dumps(message)
        )

        print(f"[ADMINISTRATOR] Wysłano wiadomość do wszystkich Ekip: {content}")

    def send_message_to_suppliers(self, content):
        message = {
            "content": content,
            "timestamp": time.time(),
            "from": "ADMINISTRATOR",
        }

        self.channel.basic_publish(
            exchange="admin_to_suppliers", routing_key="", body=json.dumps(message)
        )

        print(f"[ADMINISTRATOR] Wysłano wiadomość do wszystkich Dostawców: {content}")

    def send_message_to_all(self, content):
        message = {
            "content": content,
            "timestamp": time.time(),
            "from": "ADMINISTRATOR",
        }

        self.channel.basic_publish(
            exchange="admin_broadcast", routing_key="", body=json.dumps(message)
        )

        print(f"[ADMINISTRATOR] Wysłano wiadomość do wszystkich: {content}")

    def close(self):
        self.channel.stop_consuming()
        self.connection.close()

import threading
import time
from team import Team
from supplier import Supplier
from administrator import Administrator
from config import setup_rabbitmq


BLUE = "\033[94m"
RESET = "\033[0m"


def run_team(team_name):
    team = Team(team_name)

    listen_thread = threading.Thread(target=team.start_listening)
    listen_thread.daemon = True
    listen_thread.start()

    return team


def send_orders(team: Team, orders):
    for order in orders:
        team.send_order(order)


def run_supplier(supplier_name, equipment_types):
    supplier = Supplier(supplier_name, equipment_types)

    listen_thread = threading.Thread(target=supplier.start_listening)
    listen_thread.daemon = True
    listen_thread.start()

    return supplier


def run_administrator():
    admin = Administrator()

    channel = admin.start_listening()
    monitor_thread = threading.Thread(target=channel.start_consuming)
    monitor_thread.daemon = True
    monitor_thread.start()

    return admin


def main():
    print(f"{BLUE}Uruchamianie systemu...{RESET}")
    setup_rabbitmq()
    time.sleep(1)

    print(f"{BLUE}Uruchamianie Ekip...{RESET}")
    team1 = run_team("EKIPA1")
    team2 = run_team("EKIPA2")  # noqa: F841
    time.sleep(1)

    print(f"{BLUE}Uruchamianie Dostawców...{RESET}")
    supplier1 = run_supplier(  # noqa: F841
        "DOSTAWCA1",
        ["tlen", "buty"],
    )
    supplier2 = run_supplier(  # noqa: F841
        "DOSTAWCA2",
        ["tlen", "plecak"],
    )
    time.sleep(1)

    print(f"{BLUE}Uruchamianie Administratora...{RESET}")
    admin = run_administrator()
    time.sleep(1)

    print(f"{BLUE}Wysyłanie zleceń...{RESET}")
    send_orders(team1, ["tlen", "tlen", "buty", "buty", "plecak", "plecak"])
    time.sleep(1)

    print(f"{BLUE}Wysyłanie wiadomości od Administratora...{RESET}")
    admin.send_message_to_teams("Halo Ekipy!")
    admin.send_message_to_suppliers("Halo Dostawcy!")
    admin.send_message_to_all("Halo Ekipy i Dostawcy!")
    time.sleep(1)

    print(f"{BLUE}Zamykanie systemu...{RESET}")


if __name__ == "__main__":
    main()

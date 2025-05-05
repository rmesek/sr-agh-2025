# Zadanie I6 - Porównanie omówionych technologii middleware i usług wykorzystujących API REST oraz usług GraphQL

## Wybrane technologie

- gRPC
- REST
- GraphQL

## Warunki eksperymentu

- serwer i klient na jednej maszynie
- brak kryptograficznych zabezpieczeń komunikacji
- identyczny rozmiar danych wejściowych danych
- analogiczne interfejsy poza REST,
  gdzie uwzględniono ograniczenia tej architektury (np. over-fetching, under-fetching)
- serwer i klient napisane w Pythonie 3.12 z wykorzystaniem najpopularniejszych bibliotek:
    - gRPC:
        - **grpcio** (https://grpc.io/docs/languages/python/)
    - REST:
        - serwer: **FastAPI** (https://fastapi.tiangolo.com/)
        - klient: **requests** (https://requests.readthedocs.io/)
    - GraphQL:
        - serwer: **Strawberry + FastAPI** (https://strawberry.rocks/docs/integrations/fastapi)
        - klient: **requests** (https://requests.readthedocs.io/)

## Porównanie technologii

### Dostępne wzorce komunikacji

- gRPC
    - Unary: pojedyńcze żądania
    - Server/Client/Bidirectional streaming: przesyłanie strumieniu żądań/odpowiedzi

- REST
    - Schemat żądanie -> odpowiedź: najpopularniejszy, bezstanowy schemat komunikacji
    - Strumieniowanie wymaga dodatkowych rozwiązań
        - WebSockets: dwukierunkowe połączenie
            - (https://websockets.spec.whatwg.org/)
        - WebTransport: nowocześniejsze WebSockets z wykorzystaniem HTTP/3
            - (https://w3c.github.io/webtransport/)
        - Server-Sent Events: jednokierunkowe połączenie
            - (https://html.spec.whatwg.org/multipage/server-sent-events.html)
        - Polling: klient cyklicznie wysyła żądania do serwera
            - np. Long polling (https://en.wikipedia.org/wiki/Push_technology#Long_polling)

- GraphQL
    - Schemat Query/Mutation: podobny do REST, ale pozwala na elastyczne
      zapytania i modyfikacje danych rozwiązujące problemy over-fetching i under-fetching
        - (https://graphql.org/learn/queries/)
        - (https://graphql.org/learn/mutations/)
    - Subscriptions: pozwala na subskrypcję zdarzeń (zazwyczaj na podstawie WebSockets)
        - (https://graphql.org/learn/subscriptions/)

### Efektywność komunikacji

- gRPC
    - Format danych: Protobuf
        - binarny format danych
        - szybka serializacja
    - Komunikacja: wymaga HTTP/2
    - Kompresja: wspiera gzip, deflate

- REST
    - Format danych: JSON (najczęściej), XML
        - tekstowy format danych
        - stały rozmiar dla danego zapytania
    - Komunikacja: HTTP/1.1, HTTP/2, HTTP/3 (wykorzystuje standardowe metody HTTP)
    - Kompresja: standardowe metody HTTP jak gzip itp.

- GraphQL
    - Format danych: JSON
        - tekstowy format danych
        - możliwość dynamicznego określenia struktury danych
    - Komunikacja: zdefiniowany schemat zapytań, nie jest zależny od wersji HTTP
    - Kompresja: tak jak w REST

### Zabezpieczenia komunikacji

- gRPC (https://grpc.io/docs/guides/auth/)
    - SSL/TLS
    - ALTS: wewnętrzne zabezpieczenie przy użyciu Google Cloud
    - Token-based: zabezpieczenia oparte na tokenach np. OAuth2.0

- REST na poziomie aplikacji (https://fastapi.tiangolo.com/tutorial/security/)
    - SSL/TLS (HTTPS)
    - Token-based: zabezpieczenia oparte na tokenach np. OAuth2.0

- GraphQL na poziomie aplikacji
    - nie jest odpowiedzialny za zabezpieczenia
    - możliwości jak w REST

### Kompatybilność i interfejsy

- gRPC
    - dobrze zdefiniowane interfejsy IDL w Protobuf (`.proto`) pozwalają na generowanie kodu
    - wiele języków programowania, ale zależne od dostępności bibliotek (np. brak dla języka C)
    - eksperymentalna kompatybilność z przeglądarkami

- REST
    - brak zdefiniowanego interfejsu, ale istnieją standardy (np. OpenAPI),
      które pozwalają na automatyczne generowanie dokumentacji na podstawie kodu
    - działa z każdym klientem HTTP

- GraphQL
    - używa własnego schematu (`schema.graphql`) do definiowania interfejsów,
      może być generowany automatycznie na podstawie kodu
    - działa z każdym klientem HTTP (tylko subskrypcje mogą mieć ograniczenia)

## Wyniki eksperymentu

Eksperyment polegał na w ramach jednej sesji przesłaniu 1000 obiektów `Item` składających się z pól typów
`int`, `float` i `string`, a następnie na ich odczycie. Rozwiązania zostały zaimplementowane w typowy dla danej
metody sposób, co przede wszystkim oznacza, że w przypadku REST każdy obiekt był przesyłany jako osobne żądanie.

| Eksperyment \ Rozwiązanie             | gRPC   | REST    | GraphQL |
|---------------------------------------|--------|---------|---------|
| Łączny czas (ms)                      | 10.0   | 522.2   | 39.5    |
| Ilość przesłanych danych w L7 (bajty) | 125270 | 1071591 | 246523  |
| Czas dodania 1000 obiektów (ms)       | 1.9    | 514.1   | 20.9    |
| Rozmiar zapytania w pamięci (bajty)   | 38775  | 71669   | 73830   |
| Czas odczytania 1000 obiektów (ms)    | 0.8    | 1.6     | 11.6    |
| Rozmiar odpowiedzi w pamięci (bajty)  | 41648  | 76563   | 84583   |

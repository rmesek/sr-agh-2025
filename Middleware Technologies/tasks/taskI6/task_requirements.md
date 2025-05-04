# Zadanie I6 - Porównanie omówionych technologii middleware i usług wykorzystujących API REST oraz usług GraphQL

Celem zadania jest porównanie sposobu komunikacji stosowanego w omawianych technologiach middleware oraz usługach wykorzystujących wzorzec REST i usługach korzystających z GraphQL. Należy wziąć pod uwagę  
a) dostępne wzorce komunikacji (np. komunikacja strumieniowa w gRPC czy połączenia dwukierunkowe w ICE i ich realizowalność w jakiś sposób w każdym z rozwiązań),  
b) efektywność komunikacji pod względem ilości przesyłanych danych liczoną na poziomie L7, tj. ilość danych przesyłanych przez TCP/UDP,  
c) czas zdalnego wywołania,  
d) inne czynniki stanowiące o zaletach poszczególnych rozwiązań w stosunku do innych.  

Eksperymenty muszą być prowadzone w porównywalnych warunkach (rozmieszczenie klienta i serwera, podobny interfejs i zbiór danych), ew. trzeba uwzględnić występujące różnice (np. serwer działający lokalnie i w Internecie, kryptograficzne zabezpieczenia komunikacji i jego brak).  

Badania mogą pomijać pewne wymienione aspekty pod warunkiem dokładniejszej analizy innych (dopuszczana jest własna inwencja).  
Wynikiem prac powinien być zwarty i treściwy raport zawierający m.in. warunki eksperymentu, konkretne osiągnięte wyniki liczbowe i konkluzje. W czasie demonstracji zadania należy umieć przedyskutować najważniejsze tezy opracowania oraz wykonać podstawowe testy.  

**Technologia middleware**: gRPC oraz (REST i GraphQL)  
**Języki programowania**: wystarczy jeden  
**Maksymalna punktacja**: 10  

**Uwagi wspólne**:  
- Interfejsy IDL powinny być proste, ale zaprojektowane w sposób dojrzały (odpowiednie typy proste, właściwe wykorzystanie typów złożonych), w zadaniach aplikacyjnych dodatkowo uwzględniając możliwość wystąpienia różnego rodzaju błędów. Tam gdzie to możliwe i uzasadnione należy wykorzystać dziedziczenie interfejsów IDL.  
- Działanie aplikacji może (ale nie musi) być demonstrowane na jednej maszynie.
- Kod źródłowy zadania powinien być demonstrowany w IDE a dodatkowe elementy (np. raporty z testów) przy pomocy oprogramowania pozwalającego na wygodne i szybkie zapoznanie się z nimi.  
- Aktywność poszczególnych elementów aplikacji należy odpowiednio logować (wystarczy na konsolę) by móc sprawnie ocenić poprawność jej działania. Demonstracja może (na życzenie odbierającego) obejmować także analizę komunikacji sieciowej.  
- Aplikacja kliencka powinna mieć postać tekstową (z wyjątkiem zadania I4) i może być minimalistyczna, lecz musi pozwalać na przetestowanie funkcjonalności aplikacji szybko i na różny sposób (musi więc być przynajmniej w części interaktywna).  
- Pliki generowane (stub, skeleton, itp.) powinny się znajdować w osobnym katalogu niż kod źródłowy klienta i serwera. Pliki stanowiące wynik kompilacji (.class, .o itp) powinny być w osobnych katalogach niż pliki źródłowe.

**Sposób oceniania**:  
Wykonanie tylko jednego z zadań nie pozwoli na uzyskanie zaliczenia zadania.  
Sposób wykonania zadania będzie miał zasadniczy wpływ na ocenę. W szczególności:  
- niestarannie przygotowany interfejs IDL: -2 pkt.  
- niestarannie napisany kod (m.in. zła obsługa wyjątków, błędy działania w czasie demonstracji): -3 pkt.  
- brak aplikacji w więcej niż jednym języku programowania (gdy wymagany): -3 pkt.
- brak wymaganej funkcjonalności lub realizacja funkcjonalności w sposób niezgodny z wytycznymi: -8 pkt.  
- nieznajomość zasad działania aplikacji w zakresie omówionym na laboratoriach, w szczególności w zakresie zastosowanych mechanizmów: -10 pkt.  
- dodatkowa funkcjonalność: +3 pkt.  

Punktacja dotyczy sytuacji ekstremalnych - całkowitego braku pewnego mechanizmu albo pełnej i poprawnej implementacji - możliwe jest przyznanie części punktów (lub punktów karnych).  

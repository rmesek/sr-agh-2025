# Zadanie A2 - Subskrypcja na zdarzenia

Wynikiem prac ma być aplikacja klient-serwer w technologii gRPC.  
Klient powinien móc dokonywać subskrypcji na pewnego rodzaju zdarzenia.  
To, o czym mają one informować, jest w gestii Wykonawcy, np. o nadchodzącym wydarzeniu, którym jesteśmy zainteresowani ze względu na miejsce, czas, tematykę itp, o osiągnięciu określonych w żądaniu warunków pogodowych w danym miejscu, itp.  
Oczywiste wydaje się, że subskrypcja musi precyzyjnie określać zainteresowanie użytkownika (np. nie chcemy się subskrybować na informację o wszelkich biegach maratońskich w najbliższy weekend **na całym świecie**).  

**Dodatkowe informacje i wymagania**:  
- Na pojedyncze zdarzenie może się zasubskrybować wielu odbiorców naraz.
Może istnieć wiele niezależnych subskrypcji (tj. np. na wiele różnych instancji spotkań).  
- Projektując protokół komunikacji pomiędzy stronami należy odpowiednio wykorzystać mechanizm strumieniowania (stream) - niedopuszczalny jest polling.
- Wiadomości mogą nadchodzić z różnymi odstępami czasowymi (w rzeczywistości nawet bardzo długimi), jednak na potrzeby demonstracji rozwiązania należy przyjąć interwał rzędu pojedynczych sekund.  
- W definicji wiadomości przesyłanych do klienta należy wykorzystać pola liczbowe, enum, string, message - wraz z co najmniej jednym modyfikatorem repeated. Etap subskrypcji powinien w jakiś sposób precyzować, które powiadomienia danej usługi (spośród wszystkich) są dla odbiorcy interesujące (np. obejmować wskazanie miasta, którego warunki pogodowe nas interesują) i dany odbiorca powinien otrzymywać wyłącznie interesujące go powiadomienia.  
- Dobrze widziana będzie możliwość odsubskrybowania się z notyfikacji o wcześniej zasubskrybowanych zdarzeniach bez konieczności odłączania się klienta (ale odłączenie się musi pociągać za sobą zakończenie subskrypcji).  
- Dla uproszczenia realizacji zadania można (nie trzeba) pominąć funkcjonalność samego tworzenia instancji wydarzeń lub miejsc, których dotyczy subskrypcja i notyfikacja - może to być zawarte w pliku konfiguracyjnym, a nawet kodzie źródłowym strony serwerowej. Treść wysyłanych zdarzeń może być wynikiem działania bardzo prostego generatora.  
- W realizacji należy zadbać o odporność komunikacji na błędy sieciowe (które można symulować czasowym gwałtownym wyłączeniem klienta lub serwera lub włączeniem zapory sieciowej). Ustanie przerwy w łączności sieciowej musi pozwolić na ponowne ustanowienie komunikacji bez konieczności restartu procesów. Wiadomości przeznaczone do dostarczenia dla odbiorcy powinny być buforowane przez serwer do czasu ponownego ustanowienia łączności. Rozwiązanie musi być także "NAT-friendly" (tj. uwzględniać rozważane na laboratorium sytuacje związane z translacją adresów, w tym podtrzymywaniem aktywności w kanale komunikacyjnym) - co należy umieć udowodnić np. analizując komunikację sieciową.  

**Technologia middleware**: gRPC  
**Języki programowania**: dwa różne (jeden dla klienta, drugi dla serwera)  
**Maksymalna punktacja**: 12  

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

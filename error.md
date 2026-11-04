# error.md — przegląd kodu TheBeachLab/asteroids

Repo: https://github.com/TheBeachLab/asteroids
Klon: `asteroids/` (lokalnie, bez własnych commitów na razie)
Zweryfikowano: 2026-11-04, Python 3.14.9 + pygame-ce 2.5.7 (SDL 2.32.74), Linux x86_64

**Uwaga — dwa środowiska:** agent testuje w Python 3.14.9 + systemowy
pygame-ce 2.5.7 (bez venv). Użytkownik działa na CachyOS z **Fish shell**,
Python 3.12.13 i własnym `.venv/` (pygame-ce 2.5.8). Użytkownik uruchamia:
`cd asteroids && source .venv/bin/activate.fish && python3 src/asteroids.py`.
Wszystko, co wymaga pygame u użytkownika, musi działać w jego `.venv/`
(venv utworzony przez agenta wskazywałby na jego 3.14, a nie 3.12).

## Stan zgodności z aktualnym systemem

| Element | Wymagane | W systemie | OK? |
|---|---|---|---|
| Python | 3.x | 3.14.9 | tak — kod kompiluje się bez błędów (`py_compile`) |
| pygame | 2.x | pygame-ce 2.5.7 | tak — gra rusza (headless smoke-test) |
| `SDL_VIDEODRIVER=dummy` | test bez ekranu | działa | tak |
| `src/util/geometry.py` sam-test | asserty | przechodzi | tak |

**Gruba sprawa:** ~~gra uruchamia się poprawnie TYLKO gdy CWD = katalog `src/`
(zobacz K-1)~~ — NAPRAWIONE (2026-11-04): ścieżki aktywów są teraz
zależne od pliku (`__file__`), nie CWD. Gra rusza z dowolnego katalogu (z rootu repo,
z `src/` i z losowego CWD).

---

## Krytyczne (blokują uruchomienie / crash w grze)

### K-1. ~~Ścieżki względne do aktywów (`../res/...`) — crash poza `src/`~~ ✅ NAPRAWIONE
- `src/soundManager.py:30-38` — `pygame.mixer.Sound("../res/FIRE.WAV")` itd.
- `src/asteroids.py:204-205, 227, 235, 405` — `pygame.font.Font('../res/Hyperspace.otf', ...)`
- **Poprawka (zrealizowana 2026-11-04):**
  - `src/util/__init__.py` — nowa stała `RES_DIR` liczona z `os.path.abspath(__file__)`
    (3× `dirname`: `<root>/src/util/__init__.py` → `<root>`), więc niezależna od CWD.
  - `src/soundManager.py` — `from util import RES_DIR`, wszystkie 9 dźwięków
    przez `os.path.join(RES_DIR, "...")`.
  - `src/asteroids.py` — `from util import RES_DIR`, stała
    `FONT_PATH = os.path.join(RES_DIR, "Hyperspace.otf")`, wszystkie 6 użyciów fontu
    zmienione na `pygame.font.Font(FONT_PATH, ...)`.
- **Weryfikacja:** `py_compile` OK; headless smoke-test (5 s) przechodzi z roota repo,
  z `src/` i z losowego CWD. Font renderowany co klatkę w attract mode — crash
  przy złej ścieżce objawiłby się natychmiast.

### K-2. ~~ZeroDivisionError w `Saucer.fireBullet`~~ ✅ NAPRAWIONE
- `src/badies.py:167-168` — `mag = sqrt(dx*dx + dy*dy)` może być 0, gdy statek
  wyląduje po hiperprzestrzeni dokładnie na pozycji saucera → crash całej gry.
- **Poprawka (zrealizowana 2026-11-04):** guard `if mag < 1e-6: return` —
  bez kierunku celowania saucer pomija klatkę; `move()` wywołuje
  `fireBullet()` co klatkę, więc odda strzał, gdy statek się przesunie.
- **Weryfikacja:** test jednostkowy — statek dokładnie na saucerze: bez
  wyjątku, bez kuli; statek z odchytem: kula utworzona z poprawnym
  kierunkiem. Smoke-test gry przechodzi.

### K-3. ~~Brak `pygame.quit()` / `sys.exit` bez sprzątania~~ ✅ NAPRAWIONE
- `src/asteroids.py:247, 250` — `sys.exit(0)` przy QUIT/ESC bez `pygame.quit()`.
- **Poprawka (zrealizowana 2026-11-04):** obie ścieżki (QUIT i ESC)
  wywołują teraz `pygame.quit()` przed `sys.exit(0)`.
- **Weryfikacja:** `py_compile` OK, smoke-test gry przechodzi.

### K-4. ~~`Stage` startuje WYŁĄCZNIE w fullscreenie~~ ✅ NAPRAWIONE
- `src/stage.py:35` — `pygame.display.set_mode(dimensions, FULLSCREEN)`.
  Linia 38 (windowed) była zakomentowana. `K_f` przełącza, ale start w FS
  na systemach multi-monitor potrafi zająć nieprawidłowy monitor.
- **Poprawka (zrealizowana 2026-11-04):** `Stage.__init__` dostał parametr
  `fullscreen=False`; domyślnie okno 1024×768, `K_f` (toggle_fullscreen)
  nadal przełącza. Mysz ukrywana tylko w fullscreenie.
- **Weryfikacja:** test jednostkowy — domyślne `set_mode` dostaje flagi `0`
  (windowed), `fullscreen=True` dostaje `FULLSCREEN`; smoke-test gry przechodzi.
- (Przy okazji zamknięto M-13: `== None` → `is None`.)

### K-5. ~~Crash przy braku dostępu do audio (EPERM)~~ ✅ NAPRAWIONE
- Odkryte 2026-11-04 u użytkownika (CachyOS, PipeWire): `pygame.mixer.init()`
  rzuca `pygame.error: Couldn't set hardware audio parameters: Operation not
  permitted` → gra nie ruszała wcale, mimo że wideo działa.
- Przyczyna systemowa (u użytkownika, do zdiagnozowania): brak grupy `audio`,
  brak dostępu do `/dev/snd` lub SDL próbuje ALSA zamiast Pulse/PipeWire.
  Diagnostyka: `groups`, `systemctl --user status pipewire wireplumber`,
  `pactl info`; obejście: `SDL_AUDIODRIVER=pulseaudio python3 src/asteroids.py`.
- **Poprawka w kodzie (zrealizowana 2026-11-04):** brak audio nie może kruszyć gry.
  - `src/soundManager.py` — `initSoundManager()` owinięty w `try/except
    (pygame.error, FileNotFoundError)`; flaga modułowa `sound_available`;
    po niepowodzeniu: `sounds.clear()`, `sound_available = False`, print ostrzeżenia.
  - `playSound` / `playSoundContinuous` / `stopSound` — no-op gdy
    `sound_available` jest `False`.
  - Poza tym: usunięte nieużywane `channel = ...` (zamyka M-10).
- **Weryfikacja:** test symulacji EPERM (`pygame.mixer.init` podrasowany tak,
  żeby rzucał dokładnie ten błąd): `initSoundManager` nie rzuca,
  `sound_available=False`, `play/stop` bezpieczne; normalny ścieżka (dummy
  audio driver): 9 dźwięków wczytanych, odtwarzanie OK. Headless smoke-test
  gry przechodzi.

---

## Wysokie (bugi w logice / stabilność)

### W-1. ~~`displayScore` — format `"%02d"` nie skaluje się z wynikiem~~ ✅ NAPRAWIONE
- `src/asteroids.py:228` — przy 100+ punktach format staje się bezsensowny,
  a wynik w oryginale owijał się przy 100 000.
- **Poprawka (zrealizowana 2026-11-04):** `"%04d" % min(self.score, 99999)`.
- **Weryfikacja:** test — score 0/7/123/4200/99999/250000 renderuje
  `0000/0007/0123/4200/99999/99999` (spy na fabrykę `Font`).

### W-2. ~~`addLife` przy dużej liczbie żyć wyjeżdża poza ekran~~ ✅ NAPRAWIONE
- `src/asteroids.py:97-98` — `position.x = width - lifeNumber * rect.width - 10`;
  po kilkunastu extra life statek-wyświetlacz-życia leci w ujemne x.
- **Poprawka (zrealizowana 2026-11-04):** indeks slotu owinięty modulo
  `max(1, width // rectWidth)` — sloty cyklu się zamiast uciekać w lewo.
- **Weryfikacja:** test — 203 żyć, x w zakresie 13–1014, zero poza ekranem.

### W-3. ~~`checkCollisions` — saucer oceniany w pętli po każdej skale~~ ✅ NAPRAWIONE
- `src/asteroids.py:316-327` — blok saucera siedzi WĄTRZE pętli `for rock`,
  więc logika saucera jest sprawdzana N razy na rundę (N = liczba skal).
  Dziś działa "przypadkiem" (bullet ttl=0 po pierwszym trafieniu), ale to
  mina — np. score +500 mógłby zostać doliczony N-krotnie, gdyby `bulletCollision`
  nie zerwał ttl.
- **Poprawka (zrealizowana 2026-11-04):** blok saucera przeniesiony za pętlę
  po skalach; `ship.bulletCollision(saucer)` + score wykonywane 1×/klatkę;
  trafienia saucera w statek (body i bullets) dodatkowo za bramką safe zone.
- **Weryfikacja:** test — statek (300,400) strzela w saucer (400,400);
  po 8 `bullet.move()` + `checkCollisions` → saucer zniszczony, score == 500
  dokładnie raz.

### W-4. ~~`Rock` — klasowe `rockShape` mutowane w `createPointList`~~ ✅ NAPRAWIONE
- `src/badies.py:37, 78-80` — stan globalny (klasy) zamiast instancyjnego;
  przy przyszłej wielowątkowości / testach — chaos. Dodatkowo `pointlist`
  może pozostać niezdefiniowane, gdyby `rockShape` miało wartość spoza 1..4
  (brak `else` fallback).
- **Poprawka (zrealizowana 2026-11-04):** 4 kontury przeniesione do klasowego
  tuple `Rock.rockShapes`; każda instancja losuje `self.rockShape`
  w `__init__`; `createPointList` zwraca
  `rockShapes[max(1, min(4, shape)) - 1]` — kształty spoza 1..4 są
  przycinane do zakresu 1..4, nigdy crash ani `NameError`.
- **Weryfikacja:** test — 20 skal: wszystkie kształty 1-4 osiągalne,
  brak klasowego `rockShape`; kształty 0/5 przycinane do validnych konturów.

### W-5. ~~`Ship.draw()` ma efekt uboczny (decrement `hyperSpaceTtl`)~~ ✅ NAPRAWIONE
- `src/ship.py:54` — logika gry w metodzie rysowania; przy frame-advance w
  pauzie (K_o) czy debugowaniu draw może być wywołany więcej/mniej razy niż
  ticki.
- **Poprawka (zrealizowana 2026-11-04):** zliczanie TTL i teleport przy
  powrocie z hyperspace przeniesione do `Ship.move()` (za
  `VectorSprite.move`); `draw()` jest czysty — rysuje tylko gdy statek nie
  jest w hyperspace i zawsze zwraca `transformedPointlist`.
- **Weryfikacja:** test — `draw()` czysty (50 wywołań, ttl bez zmian);
  teleport następuje po dokładnie 100. `move()` BEZ wywołania `draw()`:
  pozycja wylosowana w granicach ekranu, kolor biały, thrustJet
  zsynchronizowany; drugi cykl hyperspace działa.

### W-6. ~~`Saucer.move` — `heading.y = heading.x` w środkowym pasie~~ ✅ NAPRAWIONE
- `src/badies.py:148-151` — saucer w pasie 33-66% szerokości leci diagonalnie
  w DOŁ w pełnej prędkości x; po opuszczeniu pasa `heading.y = 0` i saucer
  nigdy nie wraca do góry — tor jest asymetryczny (w oryginale saucer leciał
  prosto, a celował).
- **Poprawka (zrealizowana 2026-11-04):** saucer zawsze leci poziomo
  (`heading.y = 0`, brak nurkowania w pasie środkowym); strzelanie na timerze
  `shootTimer` (losowo 30-60 klatek), wypalany 1× gdy timer się zeruje,
  i tylko gdy `ship.respawnTimer <= 0` (bramka safe zone z W-7).
- **Weryfikacja:** test — 60 klatek: y nie zmienia się (100.00), 0 strzałów
  przy statku w safe zone; po `respawnTimer = 0` timer dobiega i strzela
  dokładnie 1× w cel (kierunek do statku), timer re-armowany;
  `maxBullets == 1` respektowane.

### W-7. ~~Brak strefy bezpiecznej po śmierci (TODO z kodu)~~ ✅ NAPRAWIONE
- `src/asteroids.py:21` — "safe area on new life". W oryginale statek miał
  3 s bezkolizyjności po respawnie i saucer nie atakował w strefie startu.
- **Poprawka (zrealizowana 2026-11-04):** `Ship.respawnTimer = 180` w `__init__`,
  decrement w `Ship.move()`; `checkCollisions` brankuje kolizje skal i saucera
  z statkiem przez `safe = ship.respawnTimer > 0` (strzelanie w saucer nadal
  działa w safe zone). Timer strzałów saucera (W-6) zostanie dodatkowo
  zbrankowany w W-C.
- **Weryfikacja:** test — skała przecinająca kontur statku: przy timerze >0
  statek żyje (state=playing, lives=5), po timerze=0 ginie
  (state=exploding, lives=4); timer 180→0 dokładnie po 180 `move()`, bez
  wartości ujemnych.

### W-8. ~~`lives` nie jest resetowane w `initialiseGame`~~ ✅ NAPRAWIONE
- `src/asteroids.py:62-77` — `createLivesList` robi `self.lives += 1` do
  STAREJ wartości. Dziś działa, bo gra wraca do attract_mode tylko przy
  lives == 0, ale każdy przyszły tryb (np. restart w trakcie gry, demo
  restart po timeoucie) da drift życia.
- **Poprawka (zrealizowana 2026-11-04):** `self.lives = 0` na początku
  `initialiseGame`.
- **Weryfikacja:** test — po `initialiseGame()` lives == 5 (startLives),
  nawet jeśli przed nową grą `lives == 7`; `livesList` ma 4 statki.

### W-9. ~~`Debris` — kolizje z niczym, ale TTL=50 klatek, fade 5/frame~~ ✅ NAPRAWIONE
- `src/badies.py:100-108` — OK, ale `r,g,b = self.color` + `r -= 5` bez
  `max(0, ...)` — przy zmianie TTL w przyszłości kolor pójdzie w ujemne
  wartości i `aalines` dostanie tuple z ujemnym bajtem.
- **Poprawka (zrealizowana 2026-11-04):**
  `self.color = (max(0, r-5), max(0, g-5), max(0, b-5))`.
- **Weryfikacja:** test — fade z (10,5,0) dociera do (0,0,0) i tam się
  zatrzymuje; wartości nigdy nie są ujemne.

### W-10. ~~`Bullet.move` — `shooter.bullets.remove(self)` może rzucić ValueError~~ ✅ NAPRAWIONE
- `src/shooter.py:60-63` — `Point.move` już usunął bullet ze `stage.spriteList`
  gdy ttl<=0; jeśli gdzieś w przyszłości bullet trafi też do
  `shooter.bullets` dwa razy (np. shared bullet), `remove` kruszy.
- **Poprawka (zrealizowana 2026-11-04):** `if self in self.shooter.bullets: ...remove(self)`.
- **Weryfikacja:** test — bullet z ttl=0 NIE będący w `shooter.bullets` →
  `move()` bez ValueError; bullet w liście → czyste usunięcie.

---

## Średnie (jakość / wydajność)

### M-1. Font renderowany co klatkę w `displayText` / `displayScore` / `displayPaused` / `displayFps`
- `src/asteroids.py:203-206, 227, 235, 405` — `pygame.font.Font(...).render(...)`
  co klatkę. Przy 60 FPS to 4 rendery fontu na klatkę.
- Poprawka: zainicjalizuj fonty i SURFACE tekstów w `__init__` / `Stage`,
  blituj gotowy Surface.

### M-2. `Stage.addSprite` wywołuje `sprite.draw()` (efekt uboczny)
- `src/stage.py:50-51` — `draw()` modyfikuje `transformedPointlist`;
  jeśli ktoś wywoła `addSprite` w niewłaściwej chwili, transformacja
  będzie na starej pozycji.
- Poprawka: `boundingRect = pygame.Rect(...)` z `pointlist` bez `draw()`,
  albo jawnie `sprite.rotateAndTransform()` w `addSprite`.

### M-3. `Rock.collidesWith` + `checkPolygonCollision` — podwójny koszt
- `src/asteroids.py:310-313` — najpierw `collidesWith` (rect), potem
  `checkPolygonCollision` (line-line). OK, ale `checkPolygonCollision`
  iteruje po WSZYSTKICH parach odcinków (O(n*m)), a skal ma 10-13 punktów.
- Poprawka:.spatial hash albo przynajmniej `if not collidesWith: continue`
  (już jest), ale dodatkowo `transformedPointlist` może być stale gdy draw
  nie został wywołany w tej klatce (attract mode).

### M-4. `Saucer` — `maxBullets = 1` na klasę, ale `bulletTtl = [60, 90]`
- `src/badies.py:122-123` — `maxBullets` jako klasowy atrybut = 1 dla OBU
  typów; `bulletTtl` jako lista indeksowana przez `saucerType`. OK, ale
  `maxBullets` powinien być instancyjny, żeby saucer mógł strzelić 2 razy
  bez czekania na expiry.

### M-5. `ThrustJet` — `self.ship` nie jest zresetowany przy `createNewShip`
- `src/ship.py:161-174` — `ThrustJet` trzyma referencję do `ship`; gdy
  `createNewShip` tworzy nowy statek, stary `thrustJet` jest usuwany ze
  stage, ale jeśli ktoś go reużyje (np. respawn), `ship` wskazuje na STARY
  statek.
- Poprawka: `ThrustJet.__init__` bez `ship`, albo `thrustJet.ship = newShip`
  w `createNewShip`.

### M-6. `Vector2d` — brak operatorów, brak `__eq__`, brak `__repr__`
- `src/util/vector2d.py:20-26` — kom Komentarz "needs a copy constructor".
  Bez operatorów każda operacja wektorowa to 4 linijki.
- Poprawka: `__add__`, `__sub__`, `__mul__`, `__eq__`, `__repr__`, `magnitude()`.

### M-7. `geometry.py` — `assert false` (lowercase) + `assert` w produkcyjnym kodzie
- `src/util/geometry.py:83` — `assert false` = `assert 0`; w Pythonie
  `False` (uppercase) ale i tak: `assert` w produkcyjnym kodzie jest
  wyłączane przy `-O`.
- Poprawka: `raise AssertionError("both lines vertical — impossible")`
  albo `# unreachable` komentarz.

### M-8. `geometry.py` — `str = "point was invalid  ", point` zasłania built-in
- `src/util/geometry.py:152` — `str` to built-in; po tej linii `str(...)`
  w tym作用 scope nie działa.
- Poprawka: `print(f"point was invalid: {point}")` albo `logging.warning`.

### M-9. `geometry.py` — bare `except:`
- `src/util/geometry.py:150` — łapie WSZYSTKO łącznie z `KeyboardInterrupt`
  i `SystemExit`.
- Poprawka: `except (ValueError, OverflowError):`.

### M-10. ~~`soundManager.py` — `channel = sounds[...].play()` bez użycia~~ ✅
- Zamknięte razem z K-5 (2026-11-04): `channel` nie jest już przypisywane;
  funkcje grają tylko gdy `sound_available`.

### M-11. `asteroids.py` — `frameCount` jako float, `frameCount % 10` na floatach
- `src/asteroids.py:115, 123-129` — działa, ale `frameCount` jest intem
  po co? float modulo int = float; `round(...)` OK.
- Poprawka: `frameCount = 0` (int).

### M-12. `ship.py` — `decelaration` (literówka)
- `src/ship.py:30` — `decelaration` zamiast `deceleration`.
- Poprawka: rename + aktualizacja użycia.

### M-13. ~~`stage.py` — `if dimensions == None`~~ ✅
- Zamknięte przy K-4 (2026-11-04): `if dimensions is None:`.

### M-14. ~~Brak `requirements.txt` / `pyproject.toml`~~ ✅
- Zrealizowane: `requirements.txt` z `pygame-ce>=2.5.0`, `.venv/` w `.gitignore`.
- Sposób użycia: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

### M-15. ~~Brak testów~~ ✅ NAPRAWIONE
- `src/util/geometry.py` ma self-test w `__main__`, ale reszta kodu
  nie ma żadnych testów.
- **Poprawka (zrealizowana 2026-11-04):** suita `pytest` w `tests/`
  (headless, `game` fixture na świeży stan gry na test) + workflow
  GitHub Actions `ci.yml` (Python 3.12/3.13/3.14) + `pytest.ini` i
  `requirements-dev.txt` (pytest>=8). Pokrywa wszystkie poprawki
  W-1…W-10 (plastery W-A…W-D).
- **Weryfikacja:** `python3 -m pytest -q` → 19 passed (wa=4, wb=5,
  wc=5, wd=5); CI uruchamiane na push/PR.

---

## Niskie (cosmetic / przyszłość)

### N-1. `readme.md` — "python asteroids.py" bez wskazania katalogu
- Poprawka: `cd src && python asteroids.py` albo `python src/asteroids.py`
  (po fixie K-1).

### N-2. `readme.md` — "moode" (literówka)
- `src/readme.md` — "full screen moode" → "mode".

### N-3. `asteroids.py` — `# move this kack somewhere else!`
- `src/asteroids.py:202` — "kack" → "hack"; albo po prostu przenieść
  `displayText` do osobnego modułu.

### N-4. `badies.py` — nazwa pliku (typos: "baddies"?)
- "badies" = "bad guys"? Czytaj: baddies. Poprawka: rename na
  `enemies.py` albo `badies.py` → `baddies.py` + aktualizacja importów.

### N-5. Brak `.gitignore` dla `__pycache__` / `.pyc`
- `.gitignore` istnieje, ale sprawdź czy ma `__pycache__/` i `*.pyc`.

### N-6. Brak CI
- Poprawka: GitHub Actions + `pytest` + headless smoke-test
  (`SDL_VIDEODRIVER=dummy timeout 5 python3 src/asteroids.py`).

### N-7. Brak `pyproject.toml` / package structure
- `src/` nie jest package'em (brak `setup.py` / `pyproject.toml`),
  importy są `from ship import *` — działa tylko gdy CWD=`src/`.
- Po fixie K-1 warto rozważyć `pip install -e .` albo `PYTHONPATH=src`.

---

## Priorytet napraw (proponowany kolejność)

1. ~~**K-1** (ścieżki)~~ — ✅ naprawione (2026-11-04).
2. ~~**K-5** (crash audio EPERM)~~ — ✅ naprawione w kodzie (fallback, 2026-11-04);
   diagnostyka audio u użytkownika nadal otwarta (grupa `audio`, PipeWire).
3. ~~**K-2** (ZeroDivision)~~ — ✅ naprawione (2026-11-04).
4. ~~**K-3** (pygame.quit)~~ — ✅ naprawione (2026-11-04).
5. ~~**K-4** (fullscreen)~~ — ✅ naprawione (2026-11-04, windowed domyślnie).
6. ~~**W-3** (saucer w pętli)~~ — ✅ naprawione (2026-11-04, plaster W-B).
7. ~~**W-7** (safe area)~~ — ✅ naprawione (2026-11-04, plaster W-B).
8. ~~**M-15** (testy)~~ — ✅ naprawione (2026-11-04, suita pytest + CI).
9. ~~**M-14** (requirements.txt)~~ — ✅ naprawione (2026-11-04).
10. ~~**W-1, W-2, W-8**~~ — ✅ naprawione (2026-11-04, plaster W-A).
11. ~~**W-3, W-7, W-10**~~ — ✅ naprawione (2026-11-04, plaster W-B).
12. ~~**W-4, W-6, W-9**~~ — ✅ naprawione (2026-11-04, plaster W-C).
13. ~~**W-5**~~ — ✅ naprawione (2026-11-04, plaster W-D). Blok W zamknięty.
14. Reszta M — przy okazji.

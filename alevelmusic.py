# This cell creates three user-visible files:
# 1) works.csv - cleaned, deduplicated list of classical works (Composer, Work)
# 2) create_playlist.py - a ready-to-run Spotipy script that builds a Spotify playlist from works.csv
# 3) README.txt - step-by-step setup instructions
#
# The code also prints a preview of the first few rows of works.csv

import csv
from pathlib import Path
from textwrap import dedent

# 1) Build the cleaned list (composer, work)
raw_items = [
    ("Haydn", "Symphony No. 104 in D major, \"London\""),
    ("Mendelssohn", "Symphony No. 4 in A major, \"Italian\""),
    ("Poulenc", "Trio for Oboe, Bassoon and Piano, Movement II"),
    ("Debussy", "Three Nocturnes, No. 1: Nuages"),
    # Area of study A (additional): The History of Symphony 1750-1900
    # Early Classical
    ("Stamitz", "Symphony in E-flat major, Op. 3 No. 2"),
    ("Haydn", "Symphony No. 2"),
    ("J. C. Bach", "Symphony in E-flat major, Op. 18 No. 4"),
    # Mature Classical
    ("Mozart", "Symphony No. 40 in G minor, K. 550"),
    ("Mozart", "Symphony No. 41 in C major, K. 551 \"Jupiter\""),
    ("Haydn", "Symphony No. 104 in D major, \"London\""),
    ("Beethoven", "Symphony No. 3 in E-flat major, Op. 55 \"Eroica\""),
    ("Beethoven", "Symphony No. 5 in C minor, Op. 67"),
    # Early Romantic
    ("Beethoven", "Symphony No. 6 in F major, Op. 68 \"Pastoral\""),
    ("Beethoven", "Symphony No. 7 in A major, Op. 92"),
    ("Schubert", "Symphony No. 8 in B minor, D. 759 \"Unfinished\""),
    ("Beethoven", "Symphony No. 9 in D minor, Op. 125 \"Choral\""),
    ("Berlioz", "Symphonie fantastique, Op. 14"),
    ("Mendelssohn", "Symphony No. 4 in A major, Op. 90 \"Italian\""),
    # Late Romantic
    ("Liszt", "Les préludes, S.97"),
    ("Brahms", "Symphony No. 1 in C minor, Op. 68"),
    ("Bruckner", "Symphony No. 8 in C minor, WAB 108"),
    ("Dvořák", "Symphony No. 9 in E minor, Op. 95 \"From the New World\""),
    ("Tchaikovsky", "Symphony No. 6 in B minor, Op. 74 \"Pathétique\""),
    ("Mahler", "Symphony No. 2 in C minor \"Resurrection\""),
    ("Strauss", "Also sprach Zarathustra, Op. 30"),
    # Second list (20th century composers)
    ("Berg", "4 Songs, Op. 2: No. 3"),
    ("Berg", "Wozzeck"),
    ("Berg", "Lyric Suite for String Quartet"),
    ("Berg", "Violin Concerto"),
    ("Berg", "Lulu"),
    ("Debussy", "String Quartet in G minor, L. 85"),
    ("Debussy", "Prélude à l'après-midi d'un faune"),
    ("Debussy", "Pour le piano, L. 95"),
    ("Debussy", "Pelléas et Mélisande (extracts)"),
    ("Debussy", "Préludes, Book 1 (1910) & Book 2 (1913)"),
    ("Poulenc", "Trois mouvements perpétuels"),
    ("Poulenc", "Les biches, FP 36"),
    ("Poulenc", "Concert champêtre, FP 49"),
    ("Poulenc", "Quatre poèmes de Guillaume Apollinaire, FP 58"),
    ("Poulenc", "Sextet, FP 100"),
    ("Poulenc", "Concerto for Two Pianos and Orchestra, FP 61"),
    ("Poulenc", "Flute Sonata, FP 164"),
    ("Prokofiev", "Symphony No. 1 in D major, Op. 25 \"Classical\""),
    ("Prokofiev", "The Love for Three Oranges (suite), Op. 33bis"),
    ("Prokofiev", "Romeo and Juliet (selections), Op. 64"),
    ("Prokofiev", "Symphony No. 3 in C minor, Op. 44"),
    ("Prokofiev", "Piano Concerto No. 5 in G major, Op. 55"),
    ("Prokofiev", "Violin Concerto No. 2 in G minor, Op. 63"),
    ("Ravel", "String Quartet in F major, M. 35"),
    ("Ravel", "Rapsodie espagnole, M. 54"),
    ("Ravel", "Daphnis et Chloé (suites)"),
    ("Ravel", "Le tombeau de Couperin, M. 68"),
    ("Ravel", "La valse, M. 72"),
    ("Schoenberg", "Erwartung, Op. 17"),
    ("Schoenberg", "Pierrot Lunaire, Op. 21"),
    ("Schoenberg", "String Quartet No. 3, Op. 30"),
    ("Schoenberg", "Variations for Orchestra, Op. 31"),
    ("Stravinsky", "Pulcinella (suite)"),
    ("Stravinsky", "Octet for Wind Instruments"),
    ("Stravinsky", "Concerto for Piano and Wind Instruments"),
    ("Stravinsky", "Apollo (Apollon musagète)"),
    ("Stravinsky", "Violin Concerto in D"),
    ("Stravinsky", "Duo Concertant"),
    ("Webern", "Six Bagatelles for String Quartet, Op. 9"),
    ("Webern", "Five Pieces for Orchestra, Op. 10"),
    ("Webern", "Three Lieder for Voice, E-flat Clarinet and Guitar, Op. 18"),
    ("Webern", "Concerto for Nine Instruments, Op. 24"),
]

# De-duplicate by (composer, normalized work)
def norm(s: str) -> str:
    return " ".join(s.lower().replace("’","'").replace("“","\"").replace("”","\"").split())

seen = set()
cleaned = []
for comp, work in raw_items:
    key = (norm(comp), norm(work))
    if key not in seen:
        seen.add(key)
        cleaned.append((comp, work))

data_dir = Path("/tmp/spotify_data")  # instead of Path("spotify_data") or similar
data_dir.mkdir(parents=True, exist_ok=True)

works_csv = data_dir / "works.csv"
with works_csv.open("w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["composer", "work"])
    writer.writerows(cleaned)

# 2) Create the Spotipy script
script_path = data_dir / "create_playlist.py"
script_code = dedent(r'''
    import csv
    import os
    import sys
    import time
    from urllib.parse import urlparse, parse_qs

    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    SCOPE = "playlist-modify-public playlist-modify-private"

    def normalize(s: str) -> str:
        return " ".join(s.lower().replace("’","'").split())

    def build_query(composer: str, work: str) -> str:
        # Keep it simple & robust for classical: composer + work title
        # Users can later refine recordings by editing the playlist
        return f"{composer} {work}"

    def pick_album_for_work(sp, tracks, work_hint: str):
        """
        Try to pick an album that likely contains the whole work (all movements).
        Heuristic: choose the album whose name or tracks most often include the work hint.
        """
        work_hint_n = normalize(work_hint)
        album_scores = {}

        for t in tracks:
            album = t["album"]
            album_id = album["id"]
            album_name = album["name"]
            score = 0
            if work_hint_n[:30] in normalize(album_name):
                score += 3
            if work_hint_n.split(":")[0] in normalize(album_name):
                score += 2
            album_scores[album_id] = album_scores.get(album_id, 0) + score

        # Fallback: just pick the first track's album
        if not album_scores and tracks:
            return tracks[0]["album"]["id"]
        if not album_scores:
            return None
        # choose album with highest score
        return sorted(album_scores.items(), key=lambda kv: kv[1], reverse=True)[0][0]

    def add_work(sp, user_id, playlist_id, composer, work, market="GB"):
        query = build_query(composer, work)
        results = sp.search(q=query, type="track", limit=20, market=market)
        tracks = results.get("tracks", {}).get("items", [])

        if not tracks:
            print(f"[WARN] No results for: {composer} — {work}")
            return 0

        # Try to pull all movements from a chosen album
        album_id = pick_album_for_work(sp, tracks, work_hint=work)
        if album_id:
            album = sp.album(album_id)
            album_tracks = sp.album_tracks(album_id)
            # Filter to tracks that mention the work name or its first chunk before a colon/comma
            key_part = work.split(":")[0].split(",")[0].strip()
            key_part_n = normalize(key_part)

            chosen = []
            for t in album_tracks["items"]:
                name_n = normalize(t["name"])
                if key_part_n and key_part_n[:10] in name_n:
                    chosen.append(t["uri"])

            # If our filter was too strict, just take tracks from the album that match the composer's surname or work keyword
            if not chosen:
                comp_surname = composer.split()[-1]
                comp_surname_n = normalize(comp_surname)
                for t in album_tracks["items"]:
                    name_n = normalize(t["name"])
                    if comp_surname_n in name_n or key_part_n[:6] in name_n:
                        chosen.append(t["uri"])

            # Safety fallback: add top search track if still nothing
            if not chosen:
                chosen = [tracks[0]["uri"]]

            # Add in batches of 100
            for i in range(0, len(chosen), 100):
                sp.playlist_add_items(playlist_id, chosen[i:i+100])
            print(f"[OK] Added {composer} — {work}  ({len(chosen)} tracks)")
            return len(chosen)

        # Fallback: just add the top track
        sp.playlist_add_items(playlist_id, [tracks[0]["uri"]])
        print(f"[OK] Added {composer} — {work}  (1 track)")
        return 1

    def main():
        import argparse
        parser = argparse.ArgumentParser(description="Create a Spotify playlist of classical works from works.csv")
        parser.add_argument("--csv", default="works.csv", help="Path to CSV file (composer,work)")
        parser.add_argument("--name", default="A-Level Classical Survey", help="Name of the playlist to create")
        parser.add_argument("--public", action="store_true", help="Make playlist public (default is private)")
        parser.add_argument("--market", default="GB", help="Market code for search bias (e.g., GB, US)")
        args = parser.parse_args()

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8080/callback")

        if not client_id or not client_secret:
            print("Please set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables.")
            sys.exit(1)

        auth = SpotifyOAuth(client_id=client_id,
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=SCOPE,
                            cache_path=".cache")
        sp = spotipy.Spotify(auth_manager=auth)

        me = sp.current_user()
        user_id = me["id"]

        playlist = sp.user_playlist_create(user=user_id, name=args.name, public=args.public, description="Auto-built from works.csv")
        playlist_id = playlist["id"]
        playlist_url = playlist["external_urls"]["spotify"]
        print(f"Created playlist: {playlist_url}")

        total_added = 0
        with open(args.csv, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                composer = row["composer"].strip()
                work = row["work"].strip()
                try:
                    total_added += add_work(sp, user_id, playlist_id, composer, work, market=args.market)
                    # small delay to be polite
                    time.sleep(0.25)
                except spotipy.exceptions.SpotifyException as e:
                    print(f"[ERROR] {composer} — {work}: {e}")
                except Exception as e:
                    print(f"[ERROR] {composer} — {work}: {e}")

        print(f"Done. Added ~{total_added} tracks. Playlist link: {playlist_url}")

    if __name__ == "__main__":
        main()
''')
script_path.write_text(script_code, encoding="utf-8")

# 3) README with step-by-step guide
readme_path = data_dir / "README.txt"
readme_text = dedent("""
    HOW TO CREATE YOUR SPOTIFY PLAYLIST (No passwords shared)

    1) Install Python 3.9+ if you don't have it.
    2) Open a terminal in this folder and install dependencies:
         pip install spotipy

    3) Create a free Spotify Developer app:
       - Go to https://developer.spotify.com/dashboard
       - Log in and click "Create an app".
       - App name: anything (e.g., "Playlist Builder").
       - Add Redirect URI: http://localhost:8080/callback
       - Save. Copy your Client ID and Client Secret.

    4) Set environment variables (macOS/Linux):
         export SPOTIPY_CLIENT_ID="YOUR_CLIENT_ID"
         export SPOTIPY_CLIENT_SECRET="YOUR_CLIENT_SECRET"
         export SPOTIPY_REDIRECT_URI="http://localhost:8080/callback"

       On Windows (PowerShell):
         setx SPOTIPY_CLIENT_ID "YOUR_CLIENT_ID"
         setx SPOTIPY_CLIENT_SECRET "YOUR_CLIENT_SECRET"
         setx SPOTIPY_REDIRECT_URI "http://localhost:8080/callback"
         # Then close and reopen PowerShell

    5) Run the script:
         python create_playlist.py --csv works.csv --name "A-Level Classical Survey" --public

       Your browser will open once to let you approve access. After that,
       the script will create the playlist and add the works. It prints the
       shareable Spotify link when finished.

    Notes & Tweaks (classical-specific):
      • The script tries to add ALL movements from a suitable album for each work.
        If it can't detect that, it adds the best single track as a placeholder.
      • You can re-run after editing works.csv to your taste.
      • Use --market GB or --market US to bias search results toward your region.
      • If Spotify finds multiple versions, it's normal; edit the playlist later to prefer your favourite conductor/orchestra.

    Trouble?
      • If you get "redirect_uri_mismatch", make sure the Redirect URI in the Spotify Dashboard matches exactly.
      • If nothing is added, try a different market, or simplify the work title slightly in works.csv.
""")
readme_path.write_text(readme_text, encoding="utf-8")

# Show a small preview of the works list
import pandas as pd
df = pd.read_csv(works_csv)
import streamlit as st
st.dataframe(df.head(12))

print("Files created:")
print(works_csv)
print(script_path)
print(readme_path)

from app.songs.utilities import download_and_extract_bpm

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("song_name", help="Name of the song to look for")
    parser.add_argument("artist_name", help="Name of the artist to look for")

    args = parser.parse_args()

    bpm = download_and_extract_bpm(args.song_name, args.artist_name)

    print(bpm)

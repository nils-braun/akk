import requests
from lxml import etree


def extract_bpm(content, server_object):
    """
    Internal function to extract the BPM information from the downloaded website.
    Does this by going through the HTML tree of the site.
    :param content: The HTML content as a string.
    :param server_object: a dict with at least the keys
            * iterator: The HTML tag the BPM information is encoded in
            * class_to_look_for: the name of the HTML class, this tag has
    :return: the first found bpm or None
    """
    tree = etree.HTML(content)

    bpm = None

    for td in tree.iterfind(".//{iterator}".format(iterator=server_object["iterator"])):
        if td.get("class") and server_object["class_to_look_for"] in td.get("class").split():
            bpm = int(td.text)
            break

    return bpm


def download_and_extract_bpm(song_name, artist_name):
    """
    High level function to test various websites for the given song and artist and return the first found BPM.

    :param song_name: The song name to test.
    :param artist_name: The artist name to test.
    :return: The found BPM as an integer or None.
    """
    SERVERS = [
        dict(url="https://songbpm.com/{artist_name}/{song_name}".format(
            artist_name=artist_name.replace(" ", "-").lower(),
            song_name=song_name.replace(" ", "-").lower()),
             params={}, iterator="div", class_to_look_for="number"),
        dict(url='https://www.bpmdatabase.com/music/search/',
             params={"title": song_name, "bpm": "", "genre": "", "artist": artist_name}, iterator="td",
             class_to_look_for="bpm")
    ]

    for server in SERVERS:
        bpm = download_and_extract_bpm_with_server(server_object=server)
        if bpm:
            return bpm
    return None


def download_and_extract_bpm_with_server(server_object):
    """
    Do the downloading and extraction. All the information must be encoded in the server_object, which must be
    a dictionary with the keys:
    * url: the URL to download
    * params: parameters to pass to the GET of the HTML site.
    * iterator: see extract_bpm function.
    * class_to_look_for: see extract_bpm function.
    :param server_object: See above.
    :return: the extracted BPM or None.
    """
    content = requests.get(server_object["url"], params=server_object["params"]).content
    return extract_bpm(content, server_object=server_object)
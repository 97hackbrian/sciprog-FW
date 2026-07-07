import json
import logging
import string
import time
from pathlib import Path

from scrapling.fetchers import FetcherSession

from benchmarking import benchmark
from logger import configure_logging


def extract_viewsession(page) -> dict[str, str]:
    fields = {}
    for hidden in page.css('input[type="hidden"]'):
        name = hidden.css("::attr(name)").get()
        value = hidden.css("::attr(value)").get()
        if name:
            fields[name] = value

    return fields

def main() -> None:
    url = "https://admision01.ucn.cl/directoriotelefonicoemail/Default.aspx"

    results = []

    with FetcherSession(impersonate="chrome", stealthy_headers=True, timeout=30) as session:
        # retrieve the page
        page = session.get(url)
        log.debug(f"page: {page}")

        for letter in string.ascii_uppercase:
            time.sleep(0.25)
            hidden = extract_viewsession(page)
            # log.debug(f"hidden: {hidden}")

            data = {
                **hidden,
                "iniBuscar.x": "0",
                "iniBuscar.y": "0",
                "nom": "",
                "ape": letter,
            }

            subpage = session.post(url, data=data)
            rows = subpage.css("#resultados tr")
            for row in rows:
                # log.debug(f"row {letter} -> {row}")
                cols = [c.strip() for c in row.css("td ::text, td::text").getall() if c.strip()]
                link = row.css("a::attr(href)").get()
                log.debug(f"cols: {cols} -> {link}")

                # append the name, url to the array
                people = {
                    "name": cols[0],
                    "link": link,
                }
                results.append(people)

    # save the result into ucn_directory.json
    data_file = output_dir / "results.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)


# call the main function
if __name__ == '__main__':
    configure_logging(logging.DEBUG)
    log = logging.getLogger(__name__)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")

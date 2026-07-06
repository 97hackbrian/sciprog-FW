import logging
import string
from pathlib import Path

import scrapy
from form2request import form2request
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response

from benchmarking import benchmark  # ty:ignore[unresolved-import]
from logger import configure_logging  # ty:ignore[unresolved-import]

log = logging.getLogger(__name__)


class DirectorioUCN(scrapy.Spider):
    name = "directorio_de_personas_ucn"
    start_urls = ["https://admision01.ucn.cl/directoriotelefonicoemail/Default.aspx"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 3,
    }

    def parse(self, response: Response):
        for letter in string.ascii_uppercase:
            yield form2request(
                response.css("form"),
                data={
                    "iniBuscar.x": "0",
                    "iniBuscar.y": "0",
                    "nom": "",
                    "ape": letter,
                },
                click=False,
            ).to_scrapy(self.parse_result, meta={"letter": letter})

    def parse_result(self, response: Response):
        letter = response.meta["letter"]
        rows = response.css("#resultados tr")
        persons = []

        for row in rows:
            cols = [c.strip() for c in row.css("td ::text, td::text").getall() if c.strip()]
            log.debug(f"cols: {cols}")
            link = row.css("a::attr(href)").get()
            if cols:
                person = {"datos": " | ".join(cols)}
                if link:
                    person["link"] = response.urljoin(link)
                persons.append(person)

        log.info(f"  [{letter}] {len(persons)} results")
        yield {"letra": letter, "personas": persons}


def main() -> None:
    output_file = output_dir / "ucn_directory.json"

    process = CrawlerProcess(
        settings={
            "LOG_ENABLED": False,
            "FEEDS": {
                str(output_file): {
                    "format": "json",
                    "encoding": "utf-8",
                    "overwrite": True,
                },
            },
        }
    )
    process.crawl(DirectorioUCN)
    process.start()


# call the main function
if __name__ == '__main__':
    configure_logging(logging.DEBUG)

    root_dir = Path(__file__).resolve().parent.parent
    log.debug(f"root_dir: {root_dir}")

    output_dir = root_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    log.debug(f"output_dir: {output_dir}")

    with benchmark("main", log):
        log.info("️🏎️ starting ..")
        main()
        log.info("️🏁 done.")

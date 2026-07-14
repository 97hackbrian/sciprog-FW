import logging
from pathlib import Path

import instructor
from pydantic import BaseModel, Field

from benchmarking import benchmark
from logger import configure_logging

log = logging.getLogger(__name__)


class Paper(BaseModel):
    title: str = Field(description="Paper title")
    authors: list[str] = Field(description="Paper authors")
    doi: str | None = Field(description="Paper DOI", default=None, pattern=r"^10\.\d{4,}/.+$")
    year: int = Field(description="Paper year", ge=1900, le=2026)


def main() -> None:
    # client to use llm
    client = instructor.from_provider(
        "deepseek/deepseek-chat",
        base_url="https://api.deepseek.com",
    )

    # process a paper
    # abstract = "DeepMind Lab is a first-person 3D game platform designed for research and development of general artificial intelligence and machine learning systems. DeepMind Lab can be used to study how autonomous artificial agents may learn complex tasks in large, partially observed, and visually diverse worlds. DeepMind Lab has a simple and flexible API enabling creative task-designs and novel AI-designs to be explored and quickly iterated upon. It is powered by a fast and widely recognised game engine, and tailored for effective use by the research community."
    # abstract = "Historic mudflows in Antofagasta, Chile, and their relationship to the El Niño/Southern Oscillation events. The coastal zone of the Atacama Desert is submitted to an extremely arid climate, characterized, in Antofagasta, by mean annual rainfall of 4 mm (1904-1998). However, the sporadic occurrence of heavy rainfall, together with the geomorphologic situation of the city, may produce debris and mud flows (' aluviones '). The occurrence of alluvial flows during the 20th century was investigated through the study of newspapers (available from 1916), instrumental data of precipitation (from 1904) and the observation of alluvial deposits which include anthropic remains (principally after 1900). The relationship between these evidences of alluvial activity with the occurrence of El Niño events was examined through a comparison between historical data, SOI (Southern Oscillation Index) data, and rainfall data in Antofagasta. Between 1916 and 1999, the city was affected by alluvial events in seven oportunities: 1925, 1930, twice in 1940, 1982, 1987 and 1991, with the most important episodes in 1940 and 1991. In all the cases, the rains occurred during the winter period of the developpement phase of El Niño (ENOS) events (very strong to moderate intensity), and were associated to frontal systems coming from higher latitudes, which also struck a major part of northen Chile. The convective character of the rainstorms is the cause of the great spatial zonification in the precipitations, within the same rainfall event. The comparison of annual rainfall data in Antofagasta with tendencies, at both regional and global scales, of the air temperature and the sea surface temperature, shows a coincidence between periods with more important precipitations and particular conditions, at an interdecadal scale, of the ocean-atmosphere global system. During the 20th century, alluvial episodes in the coastal area of northen Chile were coeval with periods during which a systematic increase of regional and global anomalies of the temperature of the air, and positive anomalies of the sea surface temperature were observed (between 1925 and 1942 -or 1947-, and from 1977 onwards)."
    # abstract = "Machine Learning (ML) has emerged as a pivotal technology in the operation of large and complex systems, driving advancements in fields such as autonomous vehicles, healthcare diagnostics, and financial fraud detection. Despite its benefits, the deployment of ML models brings significant security challenges, such as adversarial attacks, which can compromise the integrity and reliability of these systems. To address these challenges, this paper builds upon the concept of Secure Machine Learning Operations (SecMLOps), providing a comprehensive framework designed to integrate robust security measures throughout the entire ML operations (MLOps) lifecycle. SecMLOps builds on the principles of MLOps by embedding security considerations from the initial design phase through to deployment and continuous monitoring. This framework is particularly focused on safeguarding against sophisticated attacks that target various stages of the MLOps lifecycle, thereby enhancing the resilience and trustworthiness of ML applications. A detailed advanced pedestrian detection system (PDS) use case demonstrates the practical application of SecMLOps in securing critical MLOps. Through extensive empirical evaluations, we highlight the trade-offs between security measures and system performance, providing critical insights into optimizing security without unduly impacting operational"
    abstract = "We introduce the first work to explore web-scale diffusion models for robotics. DALL-E-Bot enables a robot to rearrange objects in a scene, by first inferring a text description of those objects, then generating an image representing a natural, human-like arrangement of those objects, and finally physically arranging the objects according to that goal image. We show that this is possible zero-shot using DALL-E, without needing any further example arrangements, data collection, or training. DALL-E-Bot is fully autonomous and is not restricted to a pre-defined set of objects or scenes, thanks to DALL-E's web-scale pre-training. Encouraging real-world results, with both human studies and objective metrics, show that integrating web-scale diffusion models into robotics pipelines is a promising direction for scalable, unsupervised robot learning."
    paper = client.create(
        messages=[
            {"role": "user", "content": abstract},
        ],
        response_model=Paper,
    )
    log.debug(f"paper: {paper}")
    log.debug(f"paper: {paper.model_dump(by_alias=True)}")
    log.debug(f"paper: {paper.model_dump_json(indent=4)}")


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

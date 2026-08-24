import logging

from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class RankingRetriever:
    """
    Retrieves structured candidates and job descriptions
    from S3 for the ranking engine.
    """

    def __init__(
        self,
        s3_service: S3Service | None = None,
    ):
        self.s3 = s3_service or S3Service()

    def get_job(
        self,
        job_id: str,
    ) -> JobDescription:
        key = f"jobs/{job_id}/jd.json"

        data = self.s3.get_json(key)

        return JobDescription.model_validate(data)

    def get_candidate(
        self,
        candidate_id: str,
    ) -> CandidateProfile:
        key = f"resumes/{candidate_id}/profile.json"

        data = self.s3.get_json(key)

        return CandidateProfile.model_validate(data)

    def get_all_candidates(self) -> list[CandidateProfile]:
        """
        Retrieve every stored candidate profile.
        """

        objects = self.s3.list_objects(
            prefix="resumes/"
        )

        candidates = []

        for obj in objects:
            key = obj["Key"]

            if not key.endswith("/profile.json"):
                continue

            try:
                data = self.s3.get_json(key)

                candidate = CandidateProfile.model_validate(
                    data
                )

                candidates.append(candidate)

            except Exception as error:
                logger.warning(
                    "Skipping invalid candidate profile at %s: %s",
                    key,
                    error,
                )
                continue

        return candidates

from src.schemas.candidate import CandidateProfile
from src.schemas.job import JobDescription
from src.services.s3_service import S3Service


class RankingRetriever:
    """
    Retrieves structured Job Descriptions and
    Candidate Profiles from S3.
    """

    def __init__(self, s3_service: S3Service | None = None):
        self.s3 = s3_service or S3Service()

    # ========================================================
    # Retrieve Job Description
    # ========================================================

    def get_job(
        self,
        job_id: str,
    ) -> JobDescription:
        """
        Load a Job Description from S3.

        Expected S3 structure:

        jobs/
            {job_id}/
                jd.json
        """

        s3_key = f"jobs/{job_id}/jd.json"

        data = self.s3.get_json(s3_key)

        return JobDescription.model_validate(data)

    # ========================================================
    # Retrieve Candidate
    # ========================================================

    def get_candidate(
        self,
        candidate_id: str,
    ) -> CandidateProfile:
        """
        Load a Candidate Profile from S3.

        Expected S3 structure:

        resumes/
            {candidate_id}/
                profile.json
        """

        s3_key = (
            f"resumes/{candidate_id}/profile.json"
        )

        data = self.s3.get_json(s3_key)

        return CandidateProfile.model_validate(data)

    # ========================================================
    # Retrieve All Candidates
    # ========================================================

    def get_all_candidates(
        self,
    ) -> list[CandidateProfile]:
        """
        Retrieve every candidate profile stored in S3.
        """

        objects = self.s3.list_objects(
            prefix="resumes/"
        )

        candidates = []

        for obj in objects:

            key = obj["Key"]

            # Only process structured profiles
            if not key.endswith("profile.json"):
                continue

            try:

                data = self.s3.get_json(key)

                candidate = (
                    CandidateProfile.model_validate(
                        data
                    )
                )

                candidates.append(candidate)

            except Exception as error:

                # One malformed candidate should
                # not stop the entire ranking process.
                print(
                    f"Skipping invalid candidate "
                    f"{key}: {error}"
                )

        return candidates

    # ========================================================
    # Retrieve Candidates For Job
    # ========================================================

    def get_candidates_for_job(
        self,
        job_id: str,
    ) -> tuple[
        JobDescription,
        list[CandidateProfile],
    ]:
        """
        Retrieve the JD and all available candidates.

        Returns:

            (
                JobDescription,
                list[CandidateProfile]
            )
        """

        job = self.get_job(job_id)

        candidates = self.get_all_candidates()

        return job, candidates
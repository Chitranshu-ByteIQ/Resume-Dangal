import os
from typing import Any

os.environ.setdefault("USE_TF", "0")


class HFService:
    """
    Lazy Sentence Transformers semantic scoring service.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    def __init__(
        self,
        model_name: str | None = None,
    ):
        self.model_name = model_name or self.MODEL_NAME
        self.device = os.getenv(
            "HF_DEVICE",
            "cpu",
        )
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )

        return self._model

    def score(
        self,
        resume_text: str,
        job_text: str,
    ) -> float:
        """
        Calculate semantic relevance as a 0-100 score.
        """

        embeddings = self.model.encode(
            [
                resume_text,
                job_text,
            ],
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

        from sentence_transformers.util import cos_sim

        similarity = cos_sim(
            embeddings[0],
            embeddings[1],
        ).item()

        return round(
            max(0.0, min(100.0, similarity * 100)),
            2,
        )

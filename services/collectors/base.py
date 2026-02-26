
from abc import ABC, abstractmethod
from domain.job import Job


class JobCollector(ABC):
    """All collectors must implement this interface."""

    @abstractmethod
    def fetch(self) -> list[Job]:
        """Fetch jobs from the source and return a list of Job objects."""
        ...
from typing import Any, List

from langchain.document_loaders.unstructured import (
    UnstructuredFileLoader, validate_unstructured_version)


class UnstructuredTSVLoader(UnstructuredFileLoader):
    """Loader that uses unstructured to load TSV files. Like other
    Unstructured loaders, UnstructuredTSVLoader can be used in both
    "single" and "elements" mode. If you use the loader in "elements"
    mode, the TSV file will be a single Unstructured Table element.
    If you use the loader in "elements" mode, an HTML representation
    of the table will be available in the "text_as_html" key in the
    document metadata.

    Examples
    --------
    from langchain.document_loaders.tsv import UnstructuredTSVLoader

    loader = UnstructuredTSVLoader("stanley-cups.tsv", mode="elements")
    docs = loader.load()
    """

    def __init__(
        self, file_path: str, mode: str = "single", **unstructured_kwargs: Any
    ):
        validate_unstructured_version(min_unstructured_version="0.7.6")
        super().__init__(file_path=file_path, mode=mode, **unstructured_kwargs)

    def _get_elements(self) -> List:
        from unstructured.partition.tsv import partition_tsv

        return partition_tsv(filename=self.file_path, **self.unstructured_kwargs)

from typing import Any, Dict, List, cast

from pydantic import Field

from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.schema import BaseRetriever, Document


class LlamaIndexRetriever(BaseRetriever):
    """Retriever for the question-answering with sources over
    an LlamaIndex data structure."""

    index: Any
    """LlamaIndex index to query."""
    query_kwargs: Dict = Field(default_factory=dict)
    """Keyword arguments to pass to the query method."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get documents relevant for a query."""
        try:
            from llama_index.indices.base import BaseGPTIndex
            from llama_index.response.schema import Response
        except ImportError:
            raise ImportError(
                "You need to install `pip install llama-index` to use this retriever."
            )
        index = cast(BaseGPTIndex, self.index)

        response = index.query(query, response_mode="no_text", **self.query_kwargs)
        response = cast(Response, response)
        # parse source nodes
        docs = []
        for source_node in response.source_nodes:
            metadata = source_node.extra_info or {}
            docs.append(
                Document(page_content=source_node.source_text, metadata=metadata)
            )
        return docs


class LlamaIndexGraphRetriever(BaseRetriever):
    """Retriever for question-answering with sources over an LlamaIndex
    graph data structure."""

    graph: Any
    """LlamaIndex graph to query."""
    query_configs: List[Dict] = Field(default_factory=list)
    """List of query configs to pass to the query method."""

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """Get documents relevant for a query."""
        try:
            from llama_index.composability.graph import (QUERY_CONFIG_TYPE,
                                                         ComposableGraph)
            from llama_index.response.schema import Response
        except ImportError:
            raise ImportError(
                "You need to install `pip install llama-index` to use this retriever."
            )
        graph = cast(ComposableGraph, self.graph)

        # for now, inject response_mode="no_text" into query configs
        for query_config in self.query_configs:
            query_config["response_mode"] = "no_text"
        query_configs = cast(List[QUERY_CONFIG_TYPE], self.query_configs)
        response = graph.query(query, query_configs=query_configs)
        response = cast(Response, response)

        # parse source nodes
        docs = []
        for source_node in response.source_nodes:
            metadata = source_node.extra_info or {}
            docs.append(
                Document(page_content=source_node.source_text, metadata=metadata)
            )
        return docs

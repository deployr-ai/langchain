from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
from uuid import uuid4
from collections import defaultdict

from pydantic import root_validator

from langchain.callbacks.manager import (
    AsyncCallbackManagerForRetrieverRun,
    CallbackManagerForRetrieverRun,
)
from langchain.docstore.document import Document
from langchain.schema import BaseRetriever


class WeaviateHybridSearchRetriever(BaseRetriever):
    """Retriever for the Weaviate's hybrid search."""

    client: Any
    """keyword arguments to pass to the Weaviate client."""
    index_name: str
    """The name of the index to use."""
    text_key: str
    """The name of the text key to use."""
    alpha: float = 0.5
    """The weight of the text key in the hybrid search."""
    k: int = 4
    """The number of results to return."""
    attributes: List[str]
    """The attributes to return in the results."""
    create_schema_if_missing: bool = True
    """Whether to create the schema if it doesn't exist."""

    @root_validator(pre=True)
    def validate_client(
        cls,
        values: Dict[str, Any],
    ) -> Dict[str, Any]:
        try:
            import weaviate
        except ImportError:
            raise ImportError(
                "Could not import weaviate python package. "
                "Please install it with `pip install weaviate-client`."
            )
        if not isinstance(values["client"], weaviate.Client):
            client = values["client"]
            raise ValueError(
                f"client should be an instance of weaviate.Client, got {type(client)}"
            )
        if values.get("attributes") is None:
            values["attributes"] = []

        cast(List, values["attributes"]).append(values["text_key"])

        if values.get("create_schema_if_missing", True):
            class_obj = {
                "class": values["index_name"],
                "properties": [{"name": values["text_key"], "dataType": ["text"]}],
                "vectorizer": "text2vec-openai",
            }

            if not values["client"].schema.exists(values["index_name"]):
                values["client"].schema.create_class(class_obj)

        return values

    class Config:
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True

    # added text_key
    def add_documents(self, docs: List[Document], **kwargs: Any) -> List[str]:
        """Upload documents to Weaviate."""
        from weaviate.util import get_valid_uuid

        with self.client.batch as batch:
            ids = []
            for i, doc in enumerate(docs):
                metadata = doc.metadata or {}
                data_properties = {self.text_key: doc.page_content, **metadata}

                # If the UUID of one of the objects already exists
                # then the existing objectwill be replaced by the new object.
                if "uuids" in kwargs:
                    _id = kwargs["uuids"][i]
                else:
                    _id = get_valid_uuid(uuid4())

                batch.add_data_object(data_properties, self.index_name, _id)
                ids.append(_id)
        return ids

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        where_filter: Optional[Dict[str, object]] = None,
        score: bool = False,
    ) -> List[Document]:
        """Look up similar documents in Weaviate."""
        query_obj = self.client.query.get(self.index_name, self.attributes)
        if where_filter:
            query_obj = query_obj.with_where(where_filter)

        if score:
            query_obj = query_obj.with_additional(["score", "explainScore"])

        result = query_obj.with_hybrid(query, alpha=self.alpha).with_limit(self.k).do()
        if "errors" in result:
            raise ValueError(f"Error during query: {result['errors']}")

        docs = []

        for res in result["data"]["Get"][self.index_name]:
            text = res.pop(self.text_key)
            docs.append(Document(page_content=text, metadata=res))
        return docs

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
        where_filter: Optional[Dict[str, object]] = None,
        score: bool = False,
    ) -> List[Document]:
        """Look up similar documents in Weaviate."""
        query_obj = self.client.query.get(self.index_name, self.attributes)
        if where_filter:
            query_obj = query_obj.with_where(where_filter)

        if score:
            query_obj = query_obj.with_additional(["score", "explainScore"])

        result = query_obj.with_hybrid(query, alpha=self.alpha).with_limit(self.k).do()
        if "errors" in result:
            raise ValueError(f"Error during query: {result['errors']}")

        docs = []

        for res in result["data"]["Get"][self.index_name]:
            text = res.pop(self.text_key)
            docs.append(Document(page_content=text, metadata=res))
        # # -- Post processing
        # sources = defaultdict(list)

        # for doc in docs:
        #     sources[doc.metadata["url"]].append((int(doc.metadata["chunkid"]), doc))

        # return_docs = []
        # for s in sources:
        #     source_list = sorted(sources[s], key=lambda x: x[0])
        #     base_cid, base_doc = source_list[0]
        #     length = 1
        #     if (base_cid != 0):
        #         base_doc.page_content = "..." + base_doc.page_content
        #     for cid, doc in source_list[1:]:
        #         if (cid - 1) != base_cid:
        #             bl = base_cid - length + 1
        #             base_doc.metadata["chunkid"] = f"{bl}-{base_cid}" if bl != base_cid else str(base_cid)
        #             base_doc.page_content = f"[DATE: {base_doc.metadata['date'][:10]}] " + base_doc.page_content
        #             return_docs.append(base_doc)
        #             length = 1
        #             base_doc = doc
        #             base_doc.page_content = "..." + base_doc.page_content
        #         else:
        #             length += 1
        #             # match strings
        #             for i in range(len(doc.page_content)):
        #                 if base_doc.page_content[-i:] == doc.page_content[:i]:
        #                     break
        #             base_doc.page_content += doc.page_content[i:]
        #         base_cid = cid
        #     bl = base_cid - length + 1
        #     base_doc.metadata["chunkid"] = f"{bl}-{base_cid}" if bl != base_cid else str(base_cid)
        #     base_doc.page_content = f"[DATE: {base_doc.metadata['date'][:10]}] " + base_doc.page_content
        #     return_docs.append(base_doc)
        # # --
        # return return_docs
        return docs

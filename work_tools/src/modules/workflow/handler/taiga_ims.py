from modules.ims.client import ImsClient
from modules.taiga.client import TaigaClient


class TaigaImsWorkflowHandler:
    """Taiga IMS workflow handler. (Facade for Taiga-IMS integration)

    Taiga User Story의 description 및 custom attribute 값에서
    IMS URL을 추출하여 연관 IMS 문서를 조회·출력하는 Facade 핸들러.
    """

    def __init__(self):
        """Initialize with TaigaClient and ImsClient instances."""
        self.taiga_client = TaigaClient()
        self.ims_client = ImsClient()
        self.util = self.ims_client.util

    # ── Common Helpers ───────────────────────────────────────────────────────

    def _resolve_us_id(self, id=None, ref=None) -> int:
        """Resolve a user story's internal ID from either an ID or a ref number."""
        if id is not None:
            return id
        if ref is None:
            raise ValueError("Either id or ref must be provided")
        resolved = self.taiga_client.get_user_story_by_ref(ref)
        print(f"Ref #{ref} → Internal ID: {resolved['id']} ({resolved['subject']})")
        return resolved["id"]

    # ── Core Logic ───────────────────────────────────────────────────────────

    def _extract_uuids_from_us(self, us_id: int) -> list[str]:
        """Extract unique IMS UUIDs from a User Story's description and custom attribute values.

        Scans the following fields for IMS URLs:
        - User Story description
        - All custom attribute values

        Args:
            us_id: The internal User Story ID.

        Returns:
            Deduplicated list of IMS UUIDs found across all fields.
        """
        us = self.taiga_client.get_user_story(us_id)
        ca_values = self.taiga_client.get_userstory_custom_attribute_values(us_id)

        # 모든 텍스트 소스 수집
        texts: list[str] = []
        if us.get("description"):
            texts.append(us["description"])
        for value in ca_values.get("attributes_values", {}).values():
            if isinstance(value, str):
                texts.append(value)

        # IMS URL 추출 후 UUID 파싱, 중복 제거 (순서 유지)
        seen: set[str] = set()
        uuids: list[str] = []
        for text in texts:
            for url in self.util.get_ims_url(text):
                uuid = self.util.parse_uuid_from_url(url)
                if uuid and uuid not in seen:
                    seen.add(uuid)
                    uuids.append(uuid)

        return uuids

    # ── Command Handlers ──────────────────────────────────────────────────────

    def get_linked_ims_docs(self, id=None, ref=None) -> None:
        """Fetch and print IMS documents linked from a Taiga User Story.

        Resolves the User Story by ID or ref, extracts all IMS UUIDs from
        the description and custom attribute values, then retrieves and
        prints each linked IMS document.

        Args:
            id: Internal Taiga User Story ID.
            ref: Taiga User Story reference number (e.g. #42).
        """
        us_id = self._resolve_us_id(id=id, ref=ref)
        uuids = self._extract_uuids_from_us(us_id)

        if not uuids:
            print("No IMS links found.")
            return

        print(f"Found {len(uuids)} IMS link(s): {', '.join(uuids)}")
        docs = self.ims_client.get_documents(uuids)
        for doc in docs:
            print(str(doc))
            print()

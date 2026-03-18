from harmonize.memory import InMemoryStore
from harmonize.models import PastMapping


class TestInMemoryStore:
    def setup_method(self):
        self.store = InMemoryStore()

    def test_store_and_retrieve(self):
        pm = PastMapping(
            target_column="fullname",
            expression="concat(firstname, lastname)",
            source_columns=["firstname", "lastname"],
        )
        self.store.store_mapping(pm)
        results = self.store.retrieve_mappings(
            target_columns=["fullname"],
            source_columns=["firstname", "lastname"],
        )
        assert "fullname" in results
        assert len(results["fullname"]) == 1
        assert results["fullname"][0].expression == "concat(firstname, lastname)"

    def test_retrieve_case_insensitive(self):
        pm = PastMapping(
            target_column="FullName",
            expression="concat(firstname, lastname)",
            source_columns=["firstname", "lastname"],
        )
        self.store.store_mapping(pm)
        results = self.store.retrieve_mappings(
            target_columns=["fullname"],
            source_columns=["firstname", "lastname"],
        )
        assert "fullname" in results

    def test_retrieve_no_match(self):
        pm = PastMapping(
            target_column="fullname",
            expression="concat(firstname, lastname)",
            source_columns=["firstname", "lastname"],
        )
        self.store.store_mapping(pm)
        results = self.store.retrieve_mappings(
            target_columns=["address"],
            source_columns=["street"],
        )
        assert len(results) == 0

    def test_multiple_mappings_same_target(self):
        pm1 = PastMapping(
            target_column="fullname",
            expression="concat(firstname, lastname)",
            source_columns=["firstname", "lastname"],
            metadata={"tags": "MFA"},
        )
        pm2 = PastMapping(
            target_column="fullname",
            expression="firstname",
            source_columns=["firstname"],
            metadata={"tags": "GSMBS"},
        )
        self.store.store_mapping(pm1)
        self.store.store_mapping(pm2)
        results = self.store.retrieve_mappings(
            target_columns=["fullname"],
            source_columns=["firstname"],
        )
        assert len(results["fullname"]) == 2

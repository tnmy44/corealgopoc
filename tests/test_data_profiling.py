from harmonize.data_profiling import SimpleDataProfiler, SimpleDataProfileMatcher
from harmonize.models import DataProfile, NumericStats, StringStats, BooleanStats


class TestSimpleDataProfiler:
    def setup_method(self):
        self.profiler = SimpleDataProfiler()

    def test_numeric_profile(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, None]
        profile = self.profiler.profile("amount", values, "numeric")
        assert profile.column_name == "amount"
        assert profile.dtype == "numeric"
        assert profile.total_count == 6
        assert profile.null_count == 1
        assert profile.unique_count == 5
        assert profile.numeric_stats is not None
        assert profile.numeric_stats.min_val == 1.0
        assert profile.numeric_stats.max_val == 5.0
        assert profile.numeric_stats.mean == 3.0

    def test_string_profile(self):
        values = ["alice", "bob", "alice", "charlie", None]
        profile = self.profiler.profile("name", values, "string")
        assert profile.total_count == 5
        assert profile.null_count == 1
        assert profile.unique_count == 3
        assert profile.string_stats is not None
        assert profile.string_stats.min_length == 3  # "bob"
        assert profile.string_stats.max_length == 7  # "charlie"
        assert profile.string_stats.most_common[0] == ("alice", 2)

    def test_boolean_profile(self):
        values = [True, False, True, True, None]
        profile = self.profiler.profile("flag", values, "boolean")
        assert profile.null_count == 1
        assert profile.boolean_stats is not None
        assert profile.boolean_stats.true_count == 3
        assert profile.boolean_stats.false_count == 1

    def test_all_nulls(self):
        values = [None, None, None]
        profile = self.profiler.profile("empty", values, "numeric")
        assert profile.null_count == 3
        assert profile.unique_count == 0
        assert profile.numeric_stats is None

    def test_empty_values(self):
        profile = self.profiler.profile("empty", [], "string")
        assert profile.total_count == 0
        assert profile.null_count == 0


class TestSimpleDataProfileMatcher:
    def setup_method(self):
        self.matcher = SimpleDataProfileMatcher()

    def test_identical_profiles(self):
        p = DataProfile("col", "numeric", 100, 10, 50,
                        numeric_stats=NumericStats(0, 100, 50, []))
        assert self.matcher.score(p, p) == 1.0

    def test_different_types(self):
        p1 = DataProfile("col", "numeric", 100, 0, 50)
        p2 = DataProfile("col", "string", 100, 0, 50)
        assert self.matcher.score(p1, p2) == 0.0

    def test_similar_numeric_profiles(self):
        p1 = DataProfile("a", "numeric", 100, 10, 50,
                         numeric_stats=NumericStats(0, 100, 48, []))
        p2 = DataProfile("b", "numeric", 100, 12, 48,
                         numeric_stats=NumericStats(0, 100, 52, []))
        score = self.matcher.score(p1, p2)
        assert score > 0.9

    def test_very_different_profiles(self):
        p1 = DataProfile("a", "numeric", 100, 0, 100,
                         numeric_stats=NumericStats(0, 10, 5, []))
        p2 = DataProfile("b", "numeric", 100, 90, 5,
                         numeric_stats=NumericStats(1000, 2000, 1500, []))
        score = self.matcher.score(p1, p2)
        assert score < 0.5

    def test_string_profiles(self):
        p1 = DataProfile("a", "string", 100, 0, 50,
                         string_stats=StringStats(3, 10, 6.0, []))
        p2 = DataProfile("b", "string", 100, 0, 50,
                         string_stats=StringStats(3, 10, 6.5, []))
        score = self.matcher.score(p1, p2)
        assert score > 0.9

    def test_boolean_profiles(self):
        p1 = DataProfile("a", "boolean", 100, 0, 2,
                         boolean_stats=BooleanStats(70, 30))
        p2 = DataProfile("b", "boolean", 100, 0, 2,
                         boolean_stats=BooleanStats(72, 28))
        score = self.matcher.score(p1, p2)
        assert score > 0.9

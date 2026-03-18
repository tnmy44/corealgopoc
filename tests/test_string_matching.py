from harmonize.string_matching import ExactStringMatcher, LevenshteinStringMatcher


class TestExactStringMatcher:
    def setup_method(self):
        self.matcher = ExactStringMatcher()

    def test_identical(self):
        assert self.matcher.score("sellerloanid", "sellerloanid") == 1.0

    def test_case_insensitive(self):
        assert self.matcher.score("SellerLoanId", "sellerloanid") == 1.0

    def test_underscore_normalization(self):
        assert self.matcher.score("seller_loan_id", "sellerloanid") == 1.0

    def test_different(self):
        assert self.matcher.score("firstname", "lastname") == 0.0

    def test_empty(self):
        assert self.matcher.score("", "") == 1.0

    def test_whitespace(self):
        assert self.matcher.score(" seller loan id ", "sellerloanid") == 1.0


class TestLevenshteinStringMatcher:
    def setup_method(self):
        self.matcher = LevenshteinStringMatcher()

    def test_identical(self):
        assert self.matcher.score("sellerloanid", "sellerloanid") == 1.0

    def test_similar(self):
        score = self.matcher.score("sellerloanid", "sellerloanld")
        assert 0.8 < score < 1.0

    def test_completely_different(self):
        score = self.matcher.score("abc", "xyz")
        assert score < 0.5

    def test_empty_strings(self):
        assert self.matcher.score("", "") == 1.0

    def test_one_empty(self):
        assert self.matcher.score("abc", "") == 0.0

    def test_substring(self):
        score = self.matcher.score("firstname", "firstnameraw")
        assert 0.5 < score < 1.0

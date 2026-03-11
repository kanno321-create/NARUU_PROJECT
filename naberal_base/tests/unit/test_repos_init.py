"""
Unit Tests for repos/__init__.py
Coverage target: 100% for module imports and exports
"""



class TestReposInit:
    """Tests for repos module initialization"""

    def test_import_plan_repo(self):
        """Test PlanRepo can be imported from repos"""
        from kis_estimator_core.repos import PlanRepo
        assert PlanRepo is not None

    def test_all_exports(self):
        """Test __all__ contains expected exports"""
        from kis_estimator_core import repos
        assert hasattr(repos, "__all__")
        assert "PlanRepo" in repos.__all__

    def test_plan_repo_class_exists(self):
        """Test PlanRepo is a class"""
        from kis_estimator_core.repos import PlanRepo
        assert isinstance(PlanRepo, type)

    def test_plan_repo_has_required_methods(self):
        """Test PlanRepo has required async methods"""
        from kis_estimator_core.repos import PlanRepo
        assert hasattr(PlanRepo, "save_plan")
        assert hasattr(PlanRepo, "load_plan")
        assert hasattr(PlanRepo, "exists")
        assert hasattr(PlanRepo, "delete_plan")

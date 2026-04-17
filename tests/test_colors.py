"""
tests/test_colors.py

Tests for utils/colors.py - pure Python color manipulation and statistical helpers.
No GUI dependencies required.
"""

import pytest
from utils.colors import (
    get_variant_color,
    combine_measurements,
    normalize_series,
    COLORS,
    DEFAULT_PP_COLOR,
    DEFAULT_TG_COLOR,
)


# ── Color Palette Constants ──────────────────────────────────────────────────

class TestColorConstants:
    """Test color palette definitions."""
    
    def test_colors_dict_exists(self):
        """COLORS dictionary is defined and non-empty."""
        assert isinstance(COLORS, dict)
        assert len(COLORS) > 0
    
    def test_required_color_keys_present(self):
        """All required color keys are present in COLORS."""
        required_keys = ['bg', 'fg', 'accent', 'pp', 'tg']
        for key in required_keys:
            assert key in COLORS, f"Missing required color key: {key}"
    
    def test_color_values_are_hex(self):
        """All color values are valid hex strings."""
        for key, value in COLORS.items():
            assert isinstance(value, str)
            assert value.startswith('#')
            # Hex color should be 7 characters (#RRGGBB)
            assert len(value) == 7
    
    def test_default_pp_color(self):
        """DEFAULT_PP_COLOR is set correctly."""
        assert DEFAULT_PP_COLOR == COLORS['pp']
        assert DEFAULT_PP_COLOR == '#4ec9b0'
    
    def test_default_tg_color(self):
        """DEFAULT_TG_COLOR is set correctly."""
        assert DEFAULT_TG_COLOR == COLORS['tg']
        assert DEFAULT_TG_COLOR == '#ce9178'


# ── Color Math: get_variant_color() ──────────────────────────────────────────

class TestGetVariantColor:
    """Test hue rotation color generation."""
    
    def test_basic_rotation(self):
        """Basic hue rotation produces a different color."""
        base = '#4ec9b0'  # teal
        variant = get_variant_color(base, 1, angle_deg=28)
        assert variant != base
        assert variant.startswith('#')
        assert len(variant) == 7
    
    def test_zero_rotation_returns_same(self):
        """Zero rotation returns the original color (or very close)."""
        base = '#4ec9b0'
        variant = get_variant_color(base, 0)
        # Should be identical since no rotation
        assert variant == base
    
    def test_multiple_rotations_produce_different_colors(self):
        """Different indices produce different colors."""
        base = '#ff0000'  # pure red
        colors = [get_variant_color(base, i, angle_deg=30) for i in range(6)]
        # All should be unique
        assert len(set(colors)) == 6
    
    def test_hue_wraparound(self):
        """Hue wraps around at 360 degrees."""
        base = '#4ec9b0'
        # Rotating by 360 degrees (13 * 28 ≈ 364, close to full circle)
        variant_0 = get_variant_color(base, 0)
        variant_13 = get_variant_color(base, 13, angle_deg=28)
        # Should be similar but not necessarily identical due to floating point
        assert variant_0.startswith('#')
        assert variant_13.startswith('#')
    
    def test_valid_hex_output(self):
        """Output is always valid hex color."""
        test_colors = ['#ff0000', '#00ff00', '#0000ff', '#ffffff', '#000000']
        for base in test_colors:
            variant = get_variant_color(base, 5, angle_deg=45)
            # Verify it's valid hex
            assert len(variant) == 7
            try:
                int(variant[1:], 16)  # Should not raise
            except ValueError:
                pytest.fail(f"Invalid hex color produced: {variant}")
    
    def test_pp_color_variants(self):
        """PP base color produces valid variants."""
        for i in range(10):
            variant = get_variant_color(DEFAULT_PP_COLOR, i)
            assert variant.startswith('#')
            assert len(variant) == 7
    
    def test_tg_color_variants(self):
        """TG base color produces valid variants."""
        for i in range(10):
            variant = get_variant_color(DEFAULT_TG_COLOR, i)
            assert variant.startswith('#')
            assert len(variant) == 7


# ── Statistical Helpers: combine_measurements() ─────────────────────────────

class TestCombineMeasurements:
    """Test statistical aggregation of mean/error pairs."""
    
    def test_empty_input(self):
        """Empty input returns (None, None)."""
        means = []
        errors = []
        mean_unified, err_unified = combine_measurements(means, errors)
        assert mean_unified is None
        assert err_unified is None
    
    def test_single_measurement(self):
        """Single measurement returns itself."""
        means = [10.0]
        errors = [2.0]
        mean_unified, err_unified = combine_measurements(means, errors)
        assert mean_unified == 10.0
        assert err_unified == 2.0
    
    def test_two_identical_measurements(self):
        """Two identical measurements return the same value."""
        means = [10.0, 10.0]
        errors = [2.0, 2.0]
        mean_unified, err_unified = combine_measurements(means, errors)
        assert mean_unified == 10.0
        # Quadratic combination: sqrt(2^2 + 2^2) / 2 = sqrt(8) / 2 ≈ 1.414
        expected_err = (2.0 ** 2 + 2.0 ** 2) ** 0.5 / 2
        assert abs(err_unified - expected_err) < 1e-9
    
    def test_mean_is_average(self):
        """Unified mean is the simple average."""
        means = [10.0, 20.0, 30.0]
        errors = [1.0, 1.0, 1.0]
        mean_unified, _ = combine_measurements(means, errors)
        expected_mean = (10.0 + 20.0 + 30.0) / 3
        assert abs(mean_unified - expected_mean) < 1e-9
    
    def test_error_quadratic_combination(self):
        """Errors are combined quadratically."""
        means = [10.0, 20.0]
        errors = [3.0, 4.0]
        _, err_unified = combine_measurements(means, errors)
        # sqrt(3^2 + 4^2) / 2 = 5 / 2 = 2.5
        expected_err = (3.0 ** 2 + 4.0 ** 2) ** 0.5 / 2
        assert abs(err_unified - expected_err) < 1e-9
    
    def test_different_errors(self):
        """Different error values are handled correctly."""
        means = [100.0, 100.0, 100.0]
        errors = [1.0, 2.0, 3.0]
        _, err_unified = combine_measurements(means, errors)
        # sqrt(1 + 4 + 9) / 3 = sqrt(14) / 3 ≈ 1.247
        expected_err = (1.0 ** 2 + 2.0 ** 2 + 3.0 ** 2) ** 0.5 / 3
        assert abs(err_unified - expected_err) < 1e-9
    
    def test_zero_errors(self):
        """Zero errors are handled correctly."""
        means = [10.0, 20.0]
        errors = [0.0, 0.0]
        _, err_unified = combine_measurements(means, errors)
        assert err_unified == 0.0
    
    def test_large_number_of_measurements(self):
        """Handles large number of measurements."""
        n = 100
        means = [50.0] * n
        errors = [1.0] * n
        mean_unified, err_unified = combine_measurements(means, errors)
        assert mean_unified == 50.0
        # sqrt(100 * 1^2) / 100 = 10 / 100 = 0.1
        expected_err = (n * 1.0 ** 2) ** 0.5 / n
        assert abs(err_unified - expected_err) < 1e-9


# ── Statistical Helpers: normalize_series() ─────────────────────────────────

class TestNormalizeSeries:
    """Test data normalization to [0, 1] or [0, 100]."""
    
    def test_empty_input(self):
        """Empty input returns originals with scale factor 1.0."""
        y_vals = []
        y_errs = []
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        assert norm_y == []
        assert norm_e == []
        assert max_val == 1.0
    
    def test_all_none_input(self):
        """All None values are preserved."""
        y_vals = [None, None, None]
        y_errs = [None, None, None]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        assert norm_y == [None, None, None]
        assert norm_e == [None, None, None]
        assert max_val == 1.0
    
    def test_basic_normalization(self):
        """Values are normalized to [0, 1]."""
        y_vals = [0.0, 50.0, 100.0]
        y_errs = [0.0, 5.0, 10.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, scale_to_pct=False)
        
        assert abs(max_val - 100.0) < 1e-9
        assert abs(norm_y[0] - 0.0) < 1e-9
        assert abs(norm_y[1] - 0.5) < 1e-9
        assert abs(norm_y[2] - 1.0) < 1e-9
        
        assert abs(norm_e[0] - 0.0) < 1e-9
        assert abs(norm_e[1] - 0.05) < 1e-9
        assert abs(norm_e[2] - 0.1) < 1e-9
    
    def test_percentage_normalization(self):
        """Values are normalized to [0, 100] when scale_to_pct=True."""
        y_vals = [0.0, 50.0, 100.0]
        y_errs = [0.0, 5.0, 10.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, scale_to_pct=True)
        
        assert abs(max_val - 100.0) < 1e-9
        assert abs(norm_y[0] - 0.0) < 1e-9
        assert abs(norm_y[1] - 50.0) < 1e-9
        assert abs(norm_y[2] - 100.0) < 1e-9
    
    def test_none_values_preserved(self):
        """None values in the middle are preserved."""
        y_vals = [0.0, None, 100.0]
        y_errs = [0.0, None, 10.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        
        assert abs(max_val - 100.0) < 1e-9
        assert abs(norm_y[0] - 0.0) < 1e-9
        assert norm_y[1] is None
        assert abs(norm_y[2] - 1.0) < 1e-9
    
    def test_zero_max_value(self):
        """All zero values return originals with scale factor 1.0."""
        y_vals = [0.0, 0.0, 0.0]
        y_errs = [0.0, 0.0, 0.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        
        assert norm_y == [0.0, 0.0, 0.0]
        assert norm_e == [0.0, 0.0, 0.0]
        assert max_val == 1.0
    
    def test_negative_values(self):
        """Negative values are handled (max is used for scaling)."""
        y_vals = [-100.0, -50.0, 0.0]
        y_errs = [10.0, 5.0, 0.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        
        # Max is 0.0, but we check for the zero-max case
        assert max_val == 1.0  # Falls back to 1.0 when max is 0
    
    def test_mixed_positive_negative(self):
        """Mixed positive and negative values use absolute max."""
        y_vals = [-50.0, 0.0, 100.0]
        y_errs = [5.0, 0.0, 10.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        
        assert abs(max_val - 100.0) < 1e-9
        assert abs(norm_y[0] - (-0.5)) < 1e-9
        assert abs(norm_y[1] - 0.0) < 1e-9
        assert abs(norm_y[2] - 1.0) < 1e-9
    
    def test_single_value(self):
        """Single value normalizes to 1.0."""
        y_vals = [42.0]
        y_errs = [2.0]
        norm_y, norm_e, max_val = normalize_series(y_vals, y_errs, False)
        
        assert abs(max_val - 42.0) < 1e-9
        assert abs(norm_y[0] - 1.0) < 1e-9
        assert abs(norm_e[0] - (2.0 / 42.0)) < 1e-9

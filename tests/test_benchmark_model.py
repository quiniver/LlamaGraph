import pytest
import os
from pathlib import Path
from model.benchmark_model import BenchmarkModel

@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_bench.csv"
    # Column names based on llamagraph.py/utils/csv_parser expectations:
    # build_commit,cpu_info,avg_ts,stddev_ts,avg_ns,stddev_ns,n_prompt,n_gen,batch,layer
    content = (
        "build_commit,cpu_info,avg_ts,stddev_ts,avg_ns,stddev_ns,n_prompt,n_gen,batch,layer\n"
        "abc123,Intel,0.5,0.01,500000000,1000,128,0,32,10\n"
        "abc123,Intel,0.6,0.02,600000000,1100,128,0,32,20\n"
    )
    csv_file.write_text(content)
    return csv_file

def test_model_load_and_dimensions(sample_csv):
    model = BenchmarkModel()
    errors = model.load_files([sample_csv])
    assert not errors
    assert model.has_data()
    assert model.get_dataset_count() == 1
    
    dims = model.get_dimensions()
    # layer and batch are the candidates from our CSV
    # Note: in our sample, 'layer' varies (10, 20), but 'batch' is constant (32).
    # However, _recompute_dimensions adds constant params to dim_vals too.
    # get_dimensions() only returns those with >1 unique value.
    assert "layer" in dims

def test_model_filters(sample_csv):
    model = BenchmarkModel()
    model.load_files([sample_csv])
    
    # Initially all values allowed
    rows = model.get_filtered_rows()
    assert len(rows) == 2
    
    # Apply filter to layer: only allow 10.0
    model.apply_filters({"layer": {10.0}})
    rows = model.get_filtered_rows()
    assert len(rows) == 1
    assert rows[0]["layer"] == 10.0
    
    # Reset filters
    model.reset_filters()
    assert len(model.get_filtered_rows()) == 2

def test_model_clear(sample_csv):
    model = BenchmarkModel()
    model.load_files([sample_csv])
    assert model.has_data()
    model.clear()
    assert not model.has_data()
    assert len(model.get_dimensions()) == 0

def test_model_observer_notification():
    model = BenchmarkModel()
    notified = False
    def callback():
        nonlocal notified
        notified = True
    
    model.add_observer(callback)
    # Loading files triggers _notify
    # We'll mock a successful parse or just use empty paths to avoid file errors if possible, 
    # but load_files is the trigger.
    # For simplicity in this test, we can't easily pass valid paths without files, 
    # so let's assume load_files with an invalid path still calls notify?
    # Looking at code: _recompute_dimensions calls _notify().
    
    # Let's try loading a non-existent file to trigger error but still proceed to recompute?
    # Actually, if parse_bench_csv returns None, it continues. 
    # If no files are valid, _datasets is empty, but _recompute_dimensions is called.
    model.load_files([Path("non_existent.csv")])
    assert notified

def test_model_get_2d_series(sample_csv):
    model = BenchmarkModel()
    model.load_files([sample_csv])
    
    # Test 2D series for 'layer' axis
    # We need to ensure the columns match what get_2d_series expects (ts_val or ns_val)
    # In our sample CSV: avg_ts is mapped to ts_val by csv_parser? 
    # Let's check csv_parser logic if possible, but assuming it works as per test_csv_parser.py
    
    series = model.get_2d_series(
        x_dim="layer",
        show_ts=True,
        show_pp=True,
        show_tg=False,
        normalize=False,
        scale_pct=False
    )
    
    assert "pp" in series
    assert len(series["pp"]) > 0
    # Check structure: {'x': ..., 'y': ..., 'err': ..., 'file_idx': ...}
    for pt in series["pp"]:
        assert "x" in pt
        assert "y" in pt
        assert "err" in pt
        assert "file_idx" in pt

def test_model_get_3d_points(sample_csv):
    model = BenchmarkModel()
    model.load_files([sample_csv])
    
    # x=layer, y=batch (though batch is constant, it's a dim)
    # We need to make sure 'batch' is treated as a dimension in the test data
    points_pp, points_tg = model.get_3d_points(
        x_dim="layer",
        y_dim="batch",
        show_ts=True,
        show_pp=True,
        show_tg=True,
        normalize=False,
        scale_pct=False
    )
    
    assert len(points_pp) > 0
    # Check structure: (x, y, z, err)
    for pt in points_pp:
        assert len(pt) == 4

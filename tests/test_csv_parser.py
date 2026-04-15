import pytest
import csv
from pathlib import Path
from utils.csv_parser import parse_bench_csv, is_llama_bench_csv

@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_bench.csv"
    content = (
        "build_commit,avg_ts,stddev_ts,avg_ns,stddev_ns,n_prompt,n_gen,layer,batch_size\n"
        "abc123,0.5,0.01,500000000,1000000,16,0,1,32\n"
        "abc123,0.6,0.02,600000000,2000000,16,0,2,32\n"
        "abc123,0.4,0.01,400000000,1000000,0,16,1,32\n"
    )
    csv_file.write_text(content)
    return csv_file

def test_is_llama_bench_csv(sample_csv, tmp_path):
    assert is_llama_bench_csv(sample_csv) is True
    
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("not a csv")
    assert is_llama_bench_csv(empty_file) is False

def test_parse_bench_csv_success(sample_csv):
    result = parse_bench_csv(sample_csv)
    assert result is not None
    assert result['source'] == str(sample_csv)
    
    # Check varying params (layer changes: 1, 2 in pp; batch_size is constant: 32)
    assert 'layer' in result['varying_params']
    assert 'batch_size' in result['constant_params']
    assert result['constant_params']['batch_size'] == '32'
    
    # Check raw rows
    # Row 1: n_prompt=16, n_gen=0 -> pp
    # Row 2: n_prompt=16, n_gen=0 -> pp
    # Row 3: n_prompt=0,  n_gen=16 -> tg
    assert len(result['raw_rows']) == 3
    assert result['raw_rows'][0]['type'] == 'pp'
    assert result['raw_rows'][2]['type'] == 'tg'
    
    # Check numeric coercion
    assert result['raw_rows'][0]['layer'] == 1.0
    assert result['raw_rows'][0]['ts_val'] == 0.5

def test_parse_bench_csv_empty(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("")
    assert parse_bench_csv(empty_file) is None

def test_parse_bench_csv_invalid_format(tmp_path):
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("garbage,data\n1,2")
    # Should return None because it won't find the required measurement columns/logic
    assert parse_bench_csv(bad_file) is None

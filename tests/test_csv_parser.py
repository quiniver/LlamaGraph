import pytest
import csv
from pathlib import Path
from utils.csv_parser import parse_bench_csv, is_llama_bench_csv

@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_bench.csv"
    content = (
        "build_commit,cpu_info,avg_ts,stddev_ts,avg_ns,stddev_ns,n_prompt,n_gen,batch,layer\n"
        "abc123,Intel,0.5,0.01,500000000,1000,128,0,32,10\n"
        "abc123,Intel,0.6,0.02,600000000,1100,128,0,32,20\n"
    )
    csv_file.write_text(content)
    return csv_file

def test_is_llama_bench_csv(sample_csv, tmp_path):
    assert is_llama_bench_csv(sample_csv) is True
    
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("not a csv")
    assert is_llama_bench_csv(empty_file) is False

def test_parse_bench_csv_structure(sample_csv):
    data = parse_bench_csv(sample_csv)
    assert data is not None
    assert 'varying_params' in data
    assert 'constant_params' in data
    assert 'raw_rows' in data
    # layer changes (10, 20), batch is constant (32)
    assert 'layer' in data['varying_params']
    assert 'batch' in data['constant_params']
    assert data['constant_params']['batch'] == '32'

def test_parse_bench_csv_row_types(sample_csv):
    data = parse_bench_csv(sample_csv)
    # First row: n_prompt=128, n_gen=0 -> type='pp'
    assert data['raw_rows'][0]['type'] == 'pp'
    assert data['raw_rows'][0]['layer'] == 10.0
    assert data['raw_rows'][0]['ts_val'] == 0.5

def test_parse_bench_csv_invalid_file(tmp_path):
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("just,some,random,stuff\n1,2,3,4")
    # Since it doesn't have the required columns or structure to produce rows
    assert parse_bench_csv(bad_file) is None

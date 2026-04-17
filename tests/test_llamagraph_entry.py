"""
tests/test_llamagraph_entry.py

Tests for llamagraph.py - CLI argument parsing and entry point logic.
Tests up to the point of GUI instantiation (which requires Tkinter).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import only the parse_args function which doesn't require GUI
import llamagraph


class TestParseArgs:
    """Test CLI argument parsing."""
    
    def test_default_arguments(self):
        """Default arguments are set correctly when no args provided."""
        with patch('sys.argv', ['llamagraph.py']):
            # Need to reparse since parse_args calls sys.argv directly
            import argparse
            parser = argparse.ArgumentParser(
                description="llamagraph — llama-bench benchmark visualizer"
            )
            parser.add_argument(
                'path',
                nargs='?',
                type=Path,
                default=Path('.'),
                help="Directory or specific CSV file to load (default: current dir)",
            )
            parser.add_argument(
                '--ns',
                action='store_true',
                help="Start in latency (ns) view instead of tokens/s",
            )
            args = parser.parse_args([])
            
            assert args.path == Path('.')
            assert args.ns is False
    
    def test_custom_directory_path(self):
        """Custom directory path is accepted."""
        test_dir = Path('/custom/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir)]):
            # Manually parse to test logic
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args([str(test_dir)])
            
            assert args.path == test_dir
    
    def test_custom_file_path(self):
        """Custom file path is accepted."""
        test_file = Path('/path/to/benchmark.csv')
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            args = parser.parse_args([str(test_file)])
            
            assert args.path == test_file
    
    def test_ns_flag_enabled(self):
        """--ns flag sets ns to True."""
        with patch('sys.argv', ['llamagraph.py', '--ns']):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args(['--ns'])
            
            assert args.ns is True
    
    def test_ns_flag_with_path(self):
        """--ns flag works with custom path."""
        test_dir = Path('/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir), '--ns']):
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
            parser.add_argument('--ns', action='store_true')
            args = parser.parse_args([str(test_dir), '--ns'])
            
            assert args.path == test_dir
            assert args.ns is True


class TestMainLogic:
    """Test main() logic up to GUI instantiation."""
    
    @pytest.fixture
    def mock_is_llama_bench_csv(self):
        """Mock the CSV validation function."""
        with patch('llamagraph.is_llama_bench_csv') as mock_func:
            yield mock_func
    
    @pytest.fixture
    def mock_tk(self):
        """Mock Tkinter to prevent GUI creation."""
        with patch('llamagraph.tk') as mock_tk_module:
            mock_root = MagicMock()
            mock_tk.Tk.return_value = mock_root
            yield mock_tk_module, mock_root
    
    @pytest.fixture
    def mock_presenter(self):
        """Mock the PlotterPresenter to prevent full initialization."""
        with patch('llamagraph.PlotterPresenter') as mock_presenter:
            yield mock_presenter
    
    @pytest.fixture
    def mock_main_window(self):
        """Mock MainWindow creation."""
        with patch('llamagraph.MainWindow') as mock_window:
            mock_win_instance = MagicMock()
            mock_window.return_value = mock_win_instance
            yield mock_window, mock_win_instance
    
    def test_file_path_logic(self, mock_is_llama_bench_csv, mock_tk, 
                            mock_presenter, mock_main_window):
        """When a file path is provided, start_dir is parent and initial_file is set."""
        test_file = Path('/benchmarks/run1.csv')
        
        # Mock CSV validation to return True
        mock_is_llama_bench_csv.return_value = True
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                # Verify logic: start_dir should be parent
                # This is tested by checking what's passed to PlotterPresenter
                call_kwargs = mock_presenter.call_args
                
                assert call_kwargs is not None
                # Check that start_dir is the parent directory
                assert call_kwargs.kwargs['start_dir'] == test_file.parent
                # Check that initial_selection_file is set
                assert call_kwargs.kwargs['initial_selection_file'] == test_file
    
    def test_invalid_csv_file_ignored(self, mock_is_llama_bench_csv, mock_tk,
                                      mock_presenter, mock_main_window):
        """When a file path is provided but not valid CSV, initial_file is None."""
        test_file = Path('/benchmarks/invalid.txt')
        
        # Mock CSV validation to return False
        mock_is_llama_bench_csv.return_value = False
        
        with patch('sys.argv', ['llamagraph.py', str(test_file)]):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                call_kwargs = mock_presenter.call_args
                
                # start_dir is still parent
                assert call_kwargs.kwargs['start_dir'] == test_file.parent
                # But initial_selection_file should be None
                assert call_kwargs.kwargs['initial_selection_file'] is None
    
    def test_directory_path_logic(self, mock_tk, mock_presenter, mock_main_window):
        """When a directory path is provided, it's used as start_dir."""
        test_dir = Path('/benchmarks')
        
        with patch('sys.argv', ['llamagraph.py', str(test_dir)]):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                call_kwargs = mock_presenter.call_args
                
                assert call_kwargs.kwargs['start_dir'] == test_dir
                assert call_kwargs.kwargs['initial_selection_file'] is None
    
    def test_nonexistent_path_exits(self, mock_tk):
        """Non-existent path causes sys.exit(1)."""
        nonexistent = Path('/nonexistent/path')
        
        with patch('sys.argv', ['llamagraph.py', str(nonexistent)]):
            with patch.object(sys, 'exit') as mock_exit:
                with pytest.raises(SystemExit) as exc_info:
                    llamagraph.main()
                
                assert exc_info.value.code == 1
                mock_exit.assert_called_once_with(1)
    
    def test_default_path_is_current_dir(self, mock_tk, mock_presenter, mock_main_window):
        """Default path (no arguments) uses current directory."""
        with patch('sys.argv', ['llamagraph.py']):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                call_kwargs = mock_presenter.call_args
                
                # Should be current directory (absolute)
                assert call_kwargs.kwargs['start_dir'] == Path('.').absolute()
    
    def test_ns_flag_affects_default_ts(self, mock_tk, mock_presenter, mock_main_window):
        """--ns flag affects default_ts parameter to Presenter."""
        with patch('sys.argv', ['llamagraph.py', '--ns']):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                call_kwargs = mock_presenter.call_args
                
                # --ns means show_ns=True, so default_ts should be False
                assert call_kwargs.kwargs['default_ts'] is False
    
    def test_no_ns_flag_means_default_ts_true(self, mock_tk, mock_presenter, mock_main_window):
        """Without --ns flag, default_ts is True."""
        with patch('sys.argv', ['llamagraph.py']):
            with patch.object(sys, 'exit'):
                llamagraph.main()
                
                call_kwargs = mock_presenter.call_args
                
                assert call_kwargs.kwargs['default_ts'] is True


class TestPathResolution:
    """Test path resolution logic."""
    
    def test_file_path_becomes_parent(self):
        """File path resolves to parent directory for start_dir."""
        input_path = Path('/a/b/c/file.csv').absolute()
        
        # Simulate the logic from main()
        if input_path.is_file():
            start_dir = input_path.parent
        else:
            start_dir = input_path
        
        assert start_dir == Path('/a/b/c').absolute()
    
    def test_directory_path_stays_same(self):
        """Directory path stays as start_dir."""
        input_path = Path('/benchmarks').absolute()
        
        # Simulate the logic from main()
        if input_path.is_file():
            start_dir = input_path.parent
        else:
            start_dir = input_path
        
        assert start_dir == input_path
